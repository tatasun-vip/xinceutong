"""
站点配置 API（容错版）
数据库失败时使用静态默认配置
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
_CACHE_TTL = 300


# 静态 fallback 配置（数据库失败时返回）
_FALLBACK_SITE_CONFIG: dict[str, dict[str, str]] = {
    "number": {
        "site.user_count": "128000",
        "site.assessment_count": "368000",
        "pay.price": "9.99",
        "site.bank_count": "10",
    },
    "text": {
        "site.brand_slogan": "别再用征信试错",
        "site.sub_slogan": "6 大产品 · 10 家银行 · 30 秒出报告",
        "site.hero_title": "30 秒测出你的真实可贷额度",
        "site.hero_subtitle": "模拟测评 · 非银行官方 · 不查征信",
        "site.cta_primary": "免费测评",
    },
    "compliance": {
        "site.disclaimer_short": "本工具仅作模拟测评，不查征信，不构成任何银行官方承诺",
        "site.disclaimer_full": "本平台所有测评结果基于您主动提供的信息模拟计算，真实贷款审批以银行/持牌金融机构官方结果为准。本工具不查央行征信报告，不向任何金融机构提交您的信息。",
    },
    "other": {},
}


@router.get("/config", summary="获取站点配置（数字+文案+合规）")
async def get_site_config(db: AsyncSession = Depends(get_db)) -> dict:
    """数据库失败时 fallback 到静态默认配置"""
    try:
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
        if not rows:
            logger.info("[site/config] DB 为空，使用静态 fallback")
            return ok(_FALLBACK_SITE_CONFIG)

        # 3. 按 group_name 分类
        grouped: dict[str, dict[str, str]] = {
            "number": {}, "text": {}, "compliance": {}, "other": {},
        }
        for r in rows:
            g = r.group_name if r.group_name in grouped else "other"
            grouped[g][r.config_key] = r.config_value

        # 4. 写缓存
        try:
            await cache_set(_CACHE_KEY, json.dumps(grouped, ensure_ascii=False), _CACHE_TTL)
        except Exception:
            pass

        return ok(grouped)
    except Exception as e:
        logger.warning(f"[site/config] DB 查询失败，使用静态 fallback: {e}")
        return ok(_FALLBACK_SITE_CONFIG)


@router.get("/config/{key}", summary="获取单个站点配置项")
async def get_site_config_by_key(key: str, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        res = await db.execute(select(SiteConfig).where(SiteConfig.config_key == key))
        row = res.scalar_one_or_none()
        if not row:
            # fallback
            value = _FALLBACK_SITE_CONFIG.get("number", {}).get(key) \
                or _FALLBACK_SITE_CONFIG.get("text", {}).get(key) \
                or _FALLBACK_SITE_CONFIG.get("compliance", {}).get(key) \
                or ""
            return ok({"key": key, "value": value, "found": bool(value)})
        return ok({
            "key": row.config_key,
            "value": row.config_value,
            "label": row.config_label,
            "group": row.group_name,
            "found": True,
        })
    except Exception as e:
        logger.warning(f"[site/config/{key}] DB 查询失败，使用静态 fallback: {e}")
        value = _FALLBACK_SITE_CONFIG.get("number", {}).get(key) \
            or _FALLBACK_SITE_CONFIG.get("text", {}).get(key) \
            or _FALLBACK_SITE_CONFIG.get("compliance", {}).get(key) \
            or ""
        return ok({"key": key, "value": value, "found": bool(value)})


@router.post("/config/refresh", summary="刷新缓存（运营改 DB 后调用）")
async def refresh_site_config_cache() -> dict:
    from app.utils.redis_client_safe import cache_delete
    try:
        await cache_delete(_CACHE_KEY)
    except Exception:
        pass
    return ok({"message": "缓存已清除，下次请求会重新加载"})
