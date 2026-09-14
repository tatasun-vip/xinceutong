"""
数据库连接：SQLAlchemy 2.x 异步引擎
支持 SQLite（本地开发）/ MySQL / PostgreSQL（生产）

Vercel Serverless 兼容：
- /var/task 只读时自动 fallback 到 /tmp/
- 没设置 DATABASE_URL 时自动用 SQLite（避免冷启动卡死）
- init_db() 失败不影响 API 启动（业务接口用静态 fallback）
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


def _resolve_sqlite_path() -> str:
    """
    解析 SQLite 路径。

    策略：
    1) 如果 DSN 已经是 sqlite → 走只读检测 fallback 到 /tmp
    2) 如果是 Vercel + 没设 DATABASE_URL → 强制走 /tmp SQLite（避免连不到 MySQL 启动失败）
    3) 其他情况 → 用原始 DSN
    """
    dsn = settings.mysql_dsn

    # 1) Vercel + 没设 DATABASE_URL → 强制 SQLite（最稳）
    is_serverless = bool(os.environ.get("VERCEL")) or bool(os.environ.get("AWS_LAMBDA_JS_RUNTIME"))
    if is_serverless and not os.environ.get("DATABASE_URL"):
        tmp_path = "/tmp/xinceutong.db"
        logger.info(f"[DB] Vercel + 无 DATABASE_URL → 强制 SQLite: {tmp_path}")
        return f"sqlite+aiosqlite:///{tmp_path}"

    # 2) DSN 不是 sqlite → 不动
    if not dsn.startswith("sqlite"):
        return dsn

    # 3) SQLite 走只读检测
    raw = dsn.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
    if raw and not raw.startswith("/") and raw != ":memory:":
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abs_path = os.path.join(backend_root, raw)
    else:
        abs_path = raw

    if is_serverless and abs_path and abs_path != ":memory:":
        try:
            test_dir = os.path.dirname(abs_path) or "."
            if os.access(test_dir, os.W_OK) is False:
                raise PermissionError("read-only")
            with open(abs_path + ".write_test", "a") as f:
                f.write("")
            os.remove(abs_path + ".write_test")
        except (PermissionError, OSError):
            tmp_path = "/tmp/xinceutong_runtime.db"
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
    _engine_kwargs.update(
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    if dsn.startswith("postgresql"):
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


async def _auto_seed_if_empty() -> None:
    """如果 SQLite 模式 + banks 表为空 → 自动跑 seed_banks 注入演示数据"""
    try:
        from app.models.bank import Bank
        from sqlalchemy import select, func
        async with AsyncSessionLocal() as session:
            count = (await session.execute(select(func.count(Bank.id)))).scalar() or 0
            if count > 0:
                logger.info(f"[DB] banks 表已有 {count} 条数据，跳过 seed")
                return
        logger.info("[DB] banks 表为空 → 自动跑 seed_banks 注入演示数据")
        # 动态 import 避免 Vercel 冷启动时把整个 seed 脚本加载进内存
        from scripts.seed_banks import main as seed_main
        await seed_main()
        logger.info("[DB] ✅ seed_banks 完成")
    except Exception as e:
        logger.warning(f"[DB] auto_seed 失败（不影响启动）: {e}")


async def init_db() -> None:
    """启动钩子：连通性探活 + 必要时 create_all + v5 P0 幂等加列 + 自动 seed

    **重要**：本函数失败不会 raise（仅 log），确保 Vercel function 不会因数据库问题整体失败
    """
    try:
        async with engine.begin() as conn:
            dsn = settings.mysql_dsn
            effective_dsn = str(engine.url)
            if effective_dsn.startswith("sqlite") or dsn.startswith("sqlite"):
                # 导入所有 model 让 Base.metadata 注册
                from app import models  # noqa: F401
                await conn.run_sync(Base.metadata.create_all)
                logger.info("SQLite 表结构已建/确认")
            else:
                # PostgreSQL / MySQL：先探活（表结构靠 alembic 迁移）
                await conn.run_sync(lambda _: None)
                logger.info(f"数据库连接成功: {dsn.split('@')[-1].split('?')[0]}")

                # ============ v5 P0 幂等迁移：自动加 dimensions 列 ============
                try:
                    res = await conn.execute(text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'assessments' AND column_name = 'dimensions'"
                    ))
                    if not res.first():
                        await conn.execute(text(
                            "ALTER TABLE assessments ADD COLUMN dimensions JSON NULL"
                        ))
                        logger.info("[v5 migration] ✅ ADD COLUMN dimensions")
                    else:
                        logger.info("[v5 migration] dimensions 列已存在，跳过")
                except Exception as mig_err:
                    logger.warning(f"[v5 migration] 跳过（{mig_err}）")

        # SQLite 模式下自动 seed（保证 /api/banks 至少能返回演示数据）
        effective_dsn = str(engine.url)
        if effective_dsn.startswith("sqlite"):
            await _auto_seed_if_empty()
    except Exception as e:
        logger.error(f"数据库初始化失败（将继续启动，API 用静态 fallback）: {e}")
        # 不 raise —— Vercel function 仍要能响应 /api/health 和静态 fallback


async def close_db() -> None:
    """关闭钩子"""
    try:
        await engine.dispose()
        logger.info("数据库连接池已关闭")
    except Exception as e:
        logger.warning(f"关闭连接池失败: {e}")


async def get_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI 依赖：每个请求一个 Session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
