"""
Alembic env：从 app.config 读取 DSN，自动 import 所有模型
支持 SQLite（本地）/ MySQL / PostgreSQL
"""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# 必须先 import app，让所有模型注册到 Base.metadata
from app.config import settings
from app.database import Base
import app.models  # noqa: F401  触发模型导入

config = context.config

# 注入异步 DSN（async_engine_from_config 要求异步 URL）
config.set_main_option("sqlalchemy.url", settings.mysql_dsn)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式（生成 SQL 脚本）"""
    context.configure(
        url=settings.mysql_sync_dsn,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """在线模式（直接连库升级）"""
    # SQLite 走同步路径（无 async 池）
    if settings.mysql_dsn.startswith("sqlite"):
        from sqlalchemy import create_engine
        connectable = create_engine(
            settings.mysql_sync_dsn,
            poolclass=pool.NullPool,
        )
        with connectable.connect() as connection:
            do_run_migrations(connection)
        connectable.dispose()
        return

    # MySQL / PostgreSQL 走异步
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
