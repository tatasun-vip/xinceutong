"""
Redis 客户端：连接池 + 异步 client
用于：评分卡配置缓存、限流防刷、订单幂等、推广码映射等

v3.1 改动（2026-09-10）：Redis 不可用时不再 raise
  - 本地开发（无 Redis）时静默降级，缓存层自然走 redis_client_safe
  - 生产环境仍建议连 Redis（限流 / 缓存命中率都依赖它）
"""
import os
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings
from app.utils.logger import logger


_redis_client: Optional[aioredis.Redis] = None
_redis_enabled: bool = True


async def init_redis() -> None:
    """启动钩子：创建连接池，探活。失败时 warn 但不 raise。"""
    global _redis_client, _redis_enabled

    # 通过环境变量 REDIS_DISABLED=1 可显式关闭（本地无 redis 时用）
    if os.environ.get("REDIS_DISABLED") == "1":
        _redis_enabled = False
        logger.warning("Redis 已通过 REDIS_DISABLED=1 关闭，进入无缓存模式")
        return

    try:
        _redis_client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
            socket_connect_timeout=2,  # 2s 超时
        )
        await _redis_client.ping()
        _redis_enabled = True
        logger.info("Redis 连接成功")
    except Exception as e:
        _redis_enabled = False
        _redis_client = None
        logger.warning(
            f"Redis 连接失败（{e}），进入无缓存模式。"
            f"生产环境请部署 Redis；本地开发可忽略。"
        )


async def close_redis() -> None:
    """关闭钩子"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis 连接已关闭")


def get_redis() -> Optional[aioredis.Redis]:
    """FastAPI 依赖：获取 redis client。未启用时返回 None。"""
    if not _redis_enabled:
        return None
    return _redis_client


def is_redis_enabled() -> bool:
    """Redis 是否可用（用于监控 / 限流判断）"""
    return _redis_enabled
