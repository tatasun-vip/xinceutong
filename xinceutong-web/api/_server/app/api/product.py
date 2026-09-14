"""
6 大产品类型 API（容错版）
数据库失败时使用静态 6 大产品配置
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product_type import ProductType
from app.utils.logger import logger
from app.utils.response import ok

router = APIRouter()


# 静态 fallback 6 大产品
_FALLBACK_PRODUCT_TYPES: list[dict] = [
    {
        "id": 1, "code": "salary_loan", "name": "工薪贷",
        "subtitle": "代发工资客户首选，利率最低",
        "user_type": "personal",
        "limit_formula": "月收入 × 24", "rate_min": 3.5, "rate_max": 6.8,
        "default_pass": 70, "focus_vars": ["monthly_income", "work_years", "employment_type"],
        "key_points": ["代发工资优待", "月收入 24 倍额度", "无需抵押"],
        "description": "针对工薪阶层设计的纯信用贷款产品。代发工资客户可享最低利率，审批快速，无需任何抵押。",
        "recommend": True, "sort_order": 1,
    },
    {
        "id": 2, "code": "house_loan", "name": "房抵贷",
        "subtitle": "房产抵押，额度高、利率低",
        "user_type": "personal",
        "limit_formula": "房产评估价 × 70%", "rate_min": 2.8, "rate_max": 4.5,
        "default_pass": 80, "focus_vars": ["has_house", "house_value", "credit_score"],
        "key_points": ["额度高至 500 万", "利率最低", "10 年期可选"],
        "description": "以房产作为抵押的贷款产品。利率在所有信用贷中最低，最高可贷房产评估价的 70%，适合有房产的客户。",
        "recommend": True, "sort_order": 2,
    },
    {
        "id": 3, "code": "business_loan", "name": "经营贷",
        "subtitle": "个体工商户、小微企业专属",
        "user_type": "business",
        "limit_formula": "经营流水 × 30%", "rate_min": 4.0, "rate_max": 7.5,
        "default_pass": 60, "focus_vars": ["business_revenue", "business_years", "tax_record"],
        "key_points": ["无需抵押", "经营流水认定", "随借随还"],
        "description": "针对个体工商户和小微企业主设计的贷款产品。根据经营流水和纳税记录核定额度，无需提供抵押物。",
        "recommend": False, "sort_order": 3,
    },
    {
        "id": 4, "code": "consumer_loan", "name": "消费贷",
        "subtitle": "日常消费，灵活使用",
        "user_type": "personal",
        "limit_formula": "月收入 × 12", "rate_min": 5.0, "rate_max": 9.5,
        "default_pass": 55, "focus_vars": ["monthly_income", "credit_score", "overdue_count_2y"],
        "key_points": ["用途灵活", "无需担保", "快速放款"],
        "description": "面向个人消费者的信用贷款产品。可用于装修、教育、医疗等任何合法消费场景，审批快速。",
        "recommend": False, "sort_order": 4,
    },
    {
        "id": 5, "code": "auto_loan", "name": "车抵贷",
        "subtitle": "车辆抵押，快速放款",
        "user_type": "personal",
        "limit_formula": "车辆评估价 × 80%", "rate_min": 4.5, "rate_max": 8.0,
        "default_pass": 65, "focus_vars": ["has_car", "car_value", "car_age"],
        "key_points": ["车辆抵押", "放款快", "不影响使用"],
        "description": "以车辆作为抵押的贷款产品。放款速度快，最快当天到账。车辆可继续正常使用，不影响日常出行。",
        "recommend": False, "sort_order": 5,
    },
    {
        "id": 6, "code": "internet_loan", "name": "互联网贷",
        "subtitle": "纯线上、秒批秒贷",
        "user_type": "personal",
        "limit_formula": "大数据风控", "rate_min": 6.0, "rate_max": 18.0,
        "default_pass": 50, "focus_vars": ["credit_score", "big_data_score"],
        "key_points": ["纯线上", "秒批秒贷", "随借随还"],
        "description": "基于大数据风控的纯线上贷款产品。无需任何面签，最快 3 分钟到账，适合应急用款。",
        "recommend": False, "sort_order": 6,
    },
]


def _to_dict(p: ProductType) -> dict:
    return {
        "id": p.id, "code": p.code, "name": p.name, "subtitle": p.subtitle,
        "user_type": p.user_type, "limit_formula": p.limit_formula,
        "rate_min": float(p.rate_min), "rate_max": float(p.rate_max),
        "default_pass": p.default_pass,
        "focus_vars": p.focus_vars or [], "key_points": p.key_points or [],
        "description": p.description, "recommend": p.recommend,
        "sort_order": p.sort_order,
    }


@router.get("", summary="获取所有启用的产品类型（按 sort_order 排序）")
async def list_product_types(
    user_type: str | None = None, db: AsyncSession = Depends(get_db)
) -> dict:
    try:
        stmt = (
            select(ProductType)
            .where(ProductType.enabled == True)  # noqa: E712
            .order_by(ProductType.sort_order.asc())
        )
        res = await db.execute(stmt)
        products = res.scalars().all()
        if not products:
            logger.info("[product-types] DB 为空，使用静态 fallback")
            items = _FALLBACK_PRODUCT_TYPES
        else:
            items = [_to_dict(p) for p in products]

        if user_type:
            items = [p for p in items if p["user_type"] == user_type]
        return ok(items)
    except Exception as e:
        logger.warning(f"[product-types] DB 查询失败，使用静态 fallback: {e}")
        items = _FALLBACK_PRODUCT_TYPES
        if user_type:
            items = [p for p in items if p["user_type"] == user_type]
        return ok(items)


@router.get("/{code}", summary="按 code 查单个产品类型")
async def get_product_type(code: str, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        res = await db.execute(
            select(ProductType).where(ProductType.code == code, ProductType.enabled == True)  # noqa: E712
        )
        p = res.scalar_one_or_none()
        if p:
            d = _to_dict(p)
            d["found"] = True
            return ok(d)
        # DB 没找到 → fallback
        for fb in _FALLBACK_PRODUCT_TYPES:
            if fb["code"] == code:
                d = dict(fb)
                d["found"] = True
                return ok(d)
        return ok({"found": False, "code": code})
    except Exception as e:
        logger.warning(f"[product-types/{code}] DB 查询失败，使用静态 fallback: {e}")
        for fb in _FALLBACK_PRODUCT_TYPES:
            if fb["code"] == code:
                d = dict(fb)
                d["found"] = True
                return ok(d)
        return ok({"found": False, "code": code})
