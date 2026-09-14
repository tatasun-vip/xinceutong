"""
银行公开 API
GET  /api/banks                      银行列表（含 logo/类型/简介）
GET  /api/banks/{code}               银行详情
GET  /api/banks/{code}/schema        银行表单 schema（5 步）
GET  /api/banks/{code}/products      银行推荐产品
"""
from typing import Any

from fastapi import APIRouter, Depends, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.database import get_db
from app.models.bank import Bank, BankFormSchema, BankProduct
from app.utils.response import ok

router = APIRouter()


@router.get("", summary="银行列表")
async def list_banks(
    type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    银行列表
    query: ?type=state_owned|joint_stock|internet|policy|city_commercial
    """
    stmt = select(Bank).where(Bank.enabled == 1).order_by(Bank.sort_order, Bank.id)
    if type:
        stmt = stmt.where(Bank.type == type)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return ok({
        "total": len(rows),
        "items": [_bank_to_dict(b) for b in rows],
    })


@router.get("/{code}", summary="银行详情")
async def get_bank(
    code: str = Path(..., description="银行编码，如 ICBC / CCB"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    bank = await _find_bank(code, db)
    return ok(_bank_to_dict(bank, full=True))


@router.get("/{code}/schema", summary="银行表单 schema（5 步）")
async def get_bank_schema(
    code: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """返回该银行 5 步问卷的完整 schema，前端动态渲染表单"""
    bank = await _find_bank(code, db)
    stmt = (
        select(BankFormSchema)
        .where(BankFormSchema.bank_id == bank.id, BankFormSchema.enabled == 1)
        .order_by(BankFormSchema.step_no, BankFormSchema.sort_order)
    )
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return ok({
        "bank_code": bank.code,
        "bank_name": bank.name,
        "total_steps": len(rows),
        "steps": [
            {
                "step_no": r.step_no,
                "step_title": r.step_title,
                "step_subtitle": r.step_subtitle,
                "step_label": r.step_label,
                "fields": r.fields_json,
            }
            for r in rows
        ],
    })


@router.get("/{code}/products", summary="银行推荐产品")
async def get_bank_products(
    code: str,
    user_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    银行推荐产品
    query: ?user_type=personal|business（可选，按用户类型过滤）

    注：当前 BankProduct 表未持久化 user_type 字段，此参数为框架就绪状态。
    数据迁移（alembic + 重新 seed）作为独立 feature 单独立项。
    """
    bank = await _find_bank(code, db)
    stmt = (
        select(BankProduct)
        .where(BankProduct.bank_id == bank.id, BankProduct.enabled == 1)
        .order_by(BankProduct.sort_order, BankProduct.id)
    )
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return ok({
        "bank_code": bank.code,
        "bank_name": bank.name,
        "total": len(rows),
        "items": [_product_to_dict(p) for p in rows],
    })


# ============================================================================
# 内部辅助
# ============================================================================


async def _find_bank(code: str, db: AsyncSession) -> Bank:
    stmt = select(Bank).where(Bank.code == code.upper(), Bank.enabled == 1)
    res = await db.execute(stmt)
    bank = res.scalar_one_or_none()
    if not bank:
        raise NotFoundException(f"银行 {code} 不存在或已下线")
    return bank


def _bank_to_dict(b: Bank, full: bool = False) -> dict[str, Any]:
    base = {
        "id": b.id,
        "code": b.code,
        "name": b.name,
        "short_name": b.short_name,
        "en_name": b.en_name,
        "type": b.type,
        "logo_url": b.logo_url,
        "short_desc": b.short_desc,
        "slogan": b.slogan,
        "brand_color": b.brand_color,
        "features": b.features or [],
    }
    if full:
        base["description"] = b.description
    return base


def _product_to_dict(p: BankProduct) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "subtitle": p.subtitle,
        "limit_min": p.limit_min,  # 万元
        "limit_max": p.limit_max,
        "rate_min": p.rate_min,
        "rate_max": p.rate_max,
        "pass_score_min": p.pass_score_min,
        "pass_score_max": p.pass_score_max,
        "features": p.features or [],
        "requirement": p.requirement,
        "recommend": bool(p.recommend),
    }
