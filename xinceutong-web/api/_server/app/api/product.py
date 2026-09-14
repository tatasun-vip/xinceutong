"""
6 大产品类型 API

前端用 /api/product-types 拉取 6 大产品配置（产品介绍页/方法论页用）
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product_type import ProductType
from app.utils.logger import logger
from app.utils.response import ok

router = APIRouter()


@router.get("", summary="获取所有启用的产品类型（按 sort_order 排序）")
async def list_product_types(
    user_type: str | None = None, db: AsyncSession = Depends(get_db)
) -> dict:
    """
    返回所有启用的产品类型
    user_type: 可选过滤 personal / business
    """
    stmt = (
        select(ProductType)
        .where(ProductType.enabled == True)  # noqa: E712
        .order_by(ProductType.sort_order.asc())
    )
    res = await db.execute(stmt)
    products = res.scalars().all()

    if user_type:
        products = [p for p in products if p.user_type == user_type]

    return ok([
        {
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "subtitle": p.subtitle,
            "user_type": p.user_type,
            "limit_formula": p.limit_formula,
            "rate_min": float(p.rate_min),
            "rate_max": float(p.rate_max),
            "default_pass": p.default_pass,
            "focus_vars": p.focus_vars or [],
            "key_points": p.key_points or [],
            "description": p.description,
            "recommend": p.recommend,
            "sort_order": p.sort_order,
        }
        for p in products
    ])


@router.get("/{code}", summary="按 code 查单个产品类型")
async def get_product_type(code: str, db: AsyncSession = Depends(get_db)) -> dict:
    res = await db.execute(
        select(ProductType).where(ProductType.code == code, ProductType.enabled == True)  # noqa: E712
    )
    p = res.scalar_one_or_none()
    if not p:
        return ok({"found": False, "code": code})

    return ok({
        "found": True,
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "subtitle": p.subtitle,
        "user_type": p.user_type,
        "limit_formula": p.limit_formula,
        "rate_min": float(p.rate_min),
        "rate_max": float(p.rate_max),
        "default_pass": p.default_pass,
        "focus_vars": p.focus_vars or [],
        "key_points": p.key_points or [],
        "description": p.description,
        "recommend": p.recommend,
    })
