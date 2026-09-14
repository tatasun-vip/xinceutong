"""
数据库连接：SQLAlchemy 2.x 异步引擎
支持 SQLite（本地开发）/ MySQL / PostgreSQL（生产）

Vercel Serverless 兼容：检测到 /var/task 只读时自动 fallback 到 /tmp/
"""
import os
import shutil
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.utils.logger import logger


class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""
    pass


def _resolve_sqlite_path() -> str | None:
    """
    解析 SQLite 路径。Vercel Serverless 的 /var/task 是只读，
    INSERT 会报 "attempt to write a readonly database" → fallback 到 /tmp/

    返回 DSN（含前缀），非 SQLite 数据库返回 None。
    """
    dsn = settings.mysql_dsn
    if not dsn.startswith("sqlite"):
        return dsn

    # 解析出原始路径（去掉前缀和 aiosqlite）
    raw = dsn.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    # 把相对路径基于 server 项目根解析为绝对
    if raw and not raw.startswith("/") and raw != ":memory:":
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abs_path = os.path.join(backend_root, raw)
    else:
        abs_path = raw

    # 在 Vercel / Lambda 环境下检测只读
    is_serverless = bool(os.environ.get("VERCEL")) or bool(os.environ.get("AWS_LAMBDA_JS_RUNTIME"))
    if is_serverless and abs_path and abs_path != ":memory:":
        # 测试只读
        try:
            test_dir = os.path.dirname(abs_path) or "."
            if os.access(test_dir, os.W_OK) is False:
                raise PermissionError("read-only")
            # 真的写一下试试
            with open(abs_path + ".write_test", "a") as f:
                f.write("")
            os.remove(abs_path + ".write_test")
        except (PermissionError, OSError):
            # fallback 到 /tmp
            tmp_path = "/tmp/xinceutong_runtime.db"
            # 冷启动时把种子库从 /var/task 复制过来
            if not os.path.exists(tmp_path) and os.path.exists(abs_path):
                try:
                    shutil.copy2(abs_path, tmp_path)
                    logger.info(f"[DB] 已将种子库从 {abs_path} 复制到 {tmp_path}")
                except Exception as e:
                    logger.warning(f"[DB] 复制种子库失败: {e}")
            logger.info(f"[DB] Vercel 只读检测：fallback 到 {tmp_path}")
            return f"sqlite+aiosqlite:///{tmp_path}"

    return dsn


# 异步引擎（FastAPI 运行时使用）
_engine_kwargs = dict(echo=settings.DEBUG)
dsn = _resolve_sqlite_path()
if not dsn.startswith("sqlite"):
    # MySQL / PostgreSQL 都需要连接池参数
    _engine_kwargs.update(
        pool_size=5,        # Render 免费层内存小，缩小
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=300,   # PG 经常 idle 杀连接，缩短回收
    )
    # PostgreSQL 关闭 SQLite 特有的 PRAGMA
    if dsn.startswith("postgresql"):
        # Render 强制 SSL
        if "ssl=" not in dsn:
            sep = "&" if "?" in dsn else "?"
            dsn = dsn + f"{sep}ssl=require"

engine = create_async_engine(dsn, **_engine_kwargs)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """启动钩子：连通性探活 + 必要时 create_all + v5 P0 幂等加列（自动 migration）"""
    try:
        async with engine.begin() as conn:
            dsn = settings.mysql_dsn
            if dsn.startswith("sqlite"):
                # 导入所有 model 让 Base.metadata 注册
                from app import models  # noqa: F401
                await conn.run_sync(Base.metadata.create_all)
                logger.info("SQLite 表结构已建/确认")
            else:
                # PostgreSQL / MySQL：先探活（表结构靠 alembic 迁移）
                await conn.run_sync(lambda _: None)
                logger.info(f"数据库连接成功: {dsn.split('@')[-1].split('?')[0]}")

                # ============ v5 P0 幂等迁移：自动加 dimensions 列 ============
                # 替代 0002_business_dimensions.sql，避免 Vercel 部署时还要手动跑 SQL
                # 用 information_schema 检测列是否存在（PG / MySQL 都支持）
                try:
                    res = await conn.execute(text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'assessments' AND column_name = 'dimensions'"
                    ))
                    if not res.first():
                        # 表存在但缺列 → 补列（PG / MySQL 语法一致）
                        await conn.execute(text(
                            "ALTER TABLE assessments ADD COLUMN dimensions JSON NULL"
                        ))
                        logger.info("[v5 migration] ✅ ADD COLUMN dimensions")
                    else:
                        logger.info("[v5 migration] dimensions 列已存在，跳过")
                except Exception as mig_err:
                    # 表可能还未初始化（首次部署）→ 不影响启动，后续 alembic 会建表
                    logger.warning(f"[v5 migration] 跳过（{mig_err}）")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise


async def close_db() -> None:
    """关闭钩子"""
    await engine.dispose()
    logger.info("数据库连接池已关闭")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：每个请求一个 Session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
