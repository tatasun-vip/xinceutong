"""
Redis 安全封装：Redis 不可用时（含显式 REDIS_DISABLED）静默降级。
所有缓存读写都 swallow 异常 / None，主流程不应被缓存故障拖死。
"""
from typing import Any, Optional

from app.redis_client import get_redis
from app.utils.logger import logger


async def cache_get(key: str) -> Optional[str]:
    """读缓存。Redis 不可用返回 None。"""
    try:
        r = get_redis()
        if r is None:
            return None
        return await r.get(key)
    except Exception as e:
        logger.warning(f"cache_get[{key}] failed: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = 600) -> bool:
    """写缓存。Redis 不可用返回 False，不阻塞主流程。"""
    try:
        r = get_redis()
        if r is None:
            return False
        await r.set(key, value, ex=ttl)
        return True
    except Exception as e:
        logger.warning(f"cache_set[{key}] failed: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """删缓存"""
    try:
        r = get_redis()
        if r is None:
            return False
        await r.delete(key)
        return True
    except Exception as e:
        logger.warning(f"cache_delete[{key}] failed: {e}")
        return False
