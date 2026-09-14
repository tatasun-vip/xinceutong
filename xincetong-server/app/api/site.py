"""
站点配置 API（数字/文案变量化）

前端用 /api/site/config 拉取所有 site_config 记录，
按 config_key 取值做运行时替换。

按 group_name 分类：
  - number: 数字（如 site.user_count, pay.price）
  - text: 文案（如 site.brand_slogan）
  - compliance: 合规（如 site.disclaimer_short）

缓存：Redis 缓存 5 分钟，运营修改后最长 5 分钟全站生效
"""
import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.site_config import SiteConfig
from app.utils.logger import logger
from app.utils.redis_client_safe import cache_get, cache_set
from app.utils.response import ok

router = APIRouter()

_CACHE_KEY = "site:config:v1"
_CACHE_TTL = 300  # 5 分钟


@router.get("/config", summary="获取站点配置（数字+文案+合规）")
async def get_site_config(db: AsyncSession = Depends(get_db)) -> dict:
    """
    返回所有站点配置，按 group_name 分类
    {
      "number": {"site.user_count": "128000", "pay.price": "9.99", ...},
      "text": {"site.brand_slogan": "别再用征信试错", ...},
      "compliance": {"site.disclaimer_short": "...", ...}
    }
    """
    # 1. 读缓存
    cached = await cache_get(_CACHE_KEY)
    if cached:
        try:
            return ok(json.loads(cached))
        except Exception as e:
            logger.warning(f"site_config 缓存反序列化失败: {e}")

    # 2. 查 DB
    res = await db.execute(select(SiteConfig))
    rows = res.scalars().all()

    # 3. 按 group_name 分类
    grouped: dict[str, dict[str, str]] = {
        "number": {},
        "text": {},
        "compliance": {},
        "other": {},
    }
    for r in rows:
        g = r.group_name if r.group_name in grouped else "other"
        grouped[g][r.config_key] = r.config_value

    # 4. 写缓存
    try:
        await cache_set(_CACHE_KEY, json.dumps(grouped, ensure_ascii=False), _CACHE_TTL)
    except Exception as e:
        logger.warning(f"site_config 缓存写失败: {e}")

    return ok(grouped)


@router.get("/config/{key}", summary="获取单个站点配置项")
async def get_site_config_by_key(key: str, db: AsyncSession = Depends(get_db)) -> dict:
    res = await db.execute(select(SiteConfig).where(SiteConfig.config_key == key))
    row = res.scalar_one_or_none()
    if not row:
        return ok({"key": key, "value": "", "found": False})
    return ok({
        "key": row.config_key,
        "value": row.config_value,
        "label": row.config_label,
        "group": row.group_name,
        "found": True,
    })


@router.post("/config/refresh", summary="刷新缓存（运营改 DB 后调用）")
async def refresh_site_config_cache() -> dict:
    from app.utils.redis_client_safe import cache_delete
    await cache_delete(_CACHE_KEY)
    logger.info("site_config 缓存已清除")
    return ok({"message": "缓存已清除，下次请求会重新加载"})
