"""
银行公开 API（容错版）
GET  /api/banks                      银行列表（含 logo/类型/简介）
GET  /api/banks/{code}               银行详情
GET  /api/banks/{code}/schema        银行表单 schema（5 步）
GET  /api/banks/{code}/products      银行推荐产品

数据库失败时 fallback 到静态 10 家银行演示数据
"""
from typing import Any

from fastapi import APIRouter, Depends, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.database import get_db
from app.models.bank import Bank, BankFormSchema, BankProduct
from app.utils.logger import logger
from app.utils.response import ok

router = APIRouter()


# ============================================================================
# 静态 Fallback（数据库失败时使用，10 家银行演示数据）
# ============================================================================
_FALLBACK_BANKS: list[dict[str, Any]] = [
    {"id": 1, "code": "ICBC", "name": "工商银行", "short_name": "工行", "en_name": "ICBC",
     "type": "state_owned", "logo_url": "/static/banks/icbc.svg",
     "short_desc": "宇宙第一大行，准入严，利率最低",
     "slogan": "宇宙行 · 利率最低", "brand_color": "#C7000B",
     "features": ["代发工资优待", "公积金专项", "利率最低", "审批严格"]},
    {"id": 2, "code": "CCB", "name": "建设银行", "short_name": "建行", "en_name": "CCB",
     "type": "state_owned", "logo_url": "/static/banks/ccb.svg",
     "short_desc": "房产抵押贷款首选",
     "slogan": "要买房 · 到建行", "brand_color": "#004B8D",
     "features": ["房产抵押利率低", "快贷速度快", "客户经理响应快"]},
    {"id": 3, "code": "BOC", "name": "中国银行", "short_name": "中行", "en_name": "BOC",
     "type": "state_owned", "logo_url": "/static/banks/boc.svg",
     "short_desc": "外汇业务见长，外贸客户首选",
     "slogan": "全球服务 · 中行", "brand_color": "#B71C1C",
     "features": ["外汇业务", "外贸专项", "国际结算"]},
    {"id": 4, "code": "ABC", "name": "农业银行", "short_name": "农行", "en_name": "ABC",
     "type": "state_owned", "logo_url": "/static/banks/abc.svg",
     "short_desc": "县乡覆盖最广，三农客户首选",
     "slogan": "服务三农 · 普惠万家", "brand_color": "#007D33",
     "features": ["三农专项", "县乡覆盖广", "惠农 e 贷"]},
    {"id": 5, "code": "BCM", "name": "交通银行", "short_name": "交行", "en_name": "BCM",
     "type": "state_owned", "logo_url": "/static/banks/bcm.svg",
     "short_desc": "财富管理见长，惠民贷额度高",
     "slogan": "惠民贷 · 财富首选", "brand_color": "#003C8F",
     "features": ["惠民贷", "财富管理", "高额度"]},
    {"id": 6, "code": "CMB", "name": "招商银行", "short_name": "招行", "en_name": "CMB",
     "type": "joint_stock", "logo_url": "/static/banks/cmb.svg",
     "short_desc": "零售之王，闪电贷最快",
     "slogan": "因您而变", "brand_color": "#A30E2A",
     "features": ["闪电贷", "零售之王", "审批快"]},
    {"id": 7, "code": "PAB", "name": "平安银行", "short_name": "平安", "en_name": "PAB",
     "type": "joint_stock", "logo_url": "/static/banks/pab.svg",
     "short_desc": "新一贷额度高，保险客户优待",
     "slogan": "新一贷 · 普惠金融", "brand_color": "#E94B3C",
     "features": ["新一贷", "保险客户", "额度高"]},
    {"id": 8, "code": "WEBANK", "name": "微众银行", "short_name": "微众", "en_name": "WeBank",
     "type": "internet", "logo_url": "/static/banks/webank.svg",
     "short_desc": "腾讯旗下，微信入口全线上",
     "slogan": "WeBank · 普惠金融", "brand_color": "#00C250",
     "features": ["全线上", "微信入口", "极速放款"]},
    {"id": 9, "code": "MYBANK", "name": "网商银行", "short_name": "网商", "en_name": "MyBank",
     "type": "internet", "logo_url": "/static/banks/mybank.svg",
     "short_desc": "阿里旗下，小微商户首选",
     "slogan": "网商贷 · 小微金融", "brand_color": "#FF6A00",
     "features": ["小微商户", "支付宝入口", "310 模式"]},
    {"id": 10, "code": "XCB", "name": "新网银行", "short_name": "新网", "en_name": "XCB",
     "type": "internet", "logo_url": "/static/banks/xcb.svg",
     "short_desc": "互联网银行三巨头之一",
     "slogan": "互联网银行 · 普惠金融", "brand_color": "#1E88E5",
     "features": ["全线上", "好人贷", "审批快"]},
]

_FALLBACK_FEATURED_FIELDS: dict[str, list[dict]] = {
    "ICBC": [{"step_no": 1, "field": "is_salary_customer", "label": "是否工行代发工资客户", "type": "switch", "weight": 15}],
    "CCB":  [{"step_no": 1, "field": "has_mortgage", "label": "是否有建行房贷", "type": "switch", "weight": 20}],
    "WEBANK": [{"step_no": 1, "field": "wechat_pay_score", "label": "微信支付分", "type": "number", "weight": 10}],
    "MYBANK": [{"step_no": 1, "field": "alipay_credit_score", "label": "支付宝信用分", "type": "number", "weight": 10}],
}


@router.get("", summary="银行列表")
async def list_banks(
    type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """银行列表（数据库失败时 fallback 到静态数据）"""
    try:
        stmt = select(Bank).where(Bank.enabled == 1).order_by(Bank.sort_order, Bank.id)
        if type:
            stmt = stmt.where(Bank.type == type)
        res = await db.execute(stmt)
        rows = res.scalars().all()
        items = [_bank_to_dict(b) for b in rows]
    except Exception as e:
        logger.warning(f"[banks] DB 查询失败，使用静态 fallback: {e}")
        items = [b for b in _FALLBACK_BANKS if (not type or b["type"] == type)]
    return ok({
        "total": len(items),
        "items": items,
    })


@router.get("/{code}", summary="银行详情")
async def get_bank(
    code: str = Path(..., description="银行编码，如 ICBC / CCB"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        bank = await _find_bank(code, db)
        return ok(_bank_to_dict(bank, full=True))
    except NotFoundException:
        raise
    except Exception as e:
        logger.warning(f"[banks/{code}] DB 查询失败，使用静态 fallback: {e}")
        # static fallback
        for b in _FALLBACK_BANKS:
            if b["code"] == code.upper():
                full = dict(b, description=b.get("short_desc", ""))
                return ok(full)
        raise NotFoundException(f"银行 {code} 不存在或已下线")


@router.get("/{code}/schema", summary="银行表单 schema（5 步）")
async def get_bank_schema(
    code: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """返回该银行 5 步问卷的完整 schema"""
    bank = None
    try:
        bank = await _find_bank(code, db)
    except NotFoundException:
        raise
    except Exception as e:
        logger.warning(f"[banks/{code}/schema] DB 查询失败，使用静态 fallback: {e}")
        for b in _FALLBACK_BANKS:
            if b["code"] == code.upper():
                bank = b
                break
        if not bank:
            raise NotFoundException(f"银行 {code} 不存在")

    # Schema steps（5 步通用模板）
    steps = [
        {
            "step_no": 1, "step_title": "基本信息", "step_subtitle": "您的身份与年龄",
            "step_label": "基础信息",
            "fields_json": _FALLBACK_FEATURED_FIELDS.get(code.upper(), []),
        },
        {
            "step_no": 2, "step_title": "工作情况", "step_subtitle": "您的收入与职业",
            "step_label": "工作情况",
            "fields_json": [
                {"field": "employment_type", "label": "工作性质", "type": "select",
                 "options": ["公务员/事业编", "国企", "上市公司", "私企", "个体工商户", "自由职业"],
                 "weight": 15},
                {"field": "monthly_income", "label": "月收入(元)", "type": "number", "weight": 20},
                {"field": "work_years", "label": "工作年限", "type": "number", "weight": 5},
            ],
        },
        {
            "step_no": 3, "step_title": "资产情况", "step_subtitle": "您的资产与负债",
            "step_label": "资产情况",
            "fields_json": [
                {"field": "has_house", "label": "是否有房产", "type": "switch", "weight": 10},
                {"field": "has_car", "label": "是否有车产", "type": "switch", "weight": 5},
                {"field": "credit_card_debt", "label": "信用卡未还余额(元)", "type": "number", "weight": 10},
            ],
        },
        {
            "step_no": 4, "step_title": "信用记录", "step_subtitle": "您的征信情况",
            "step_label": "信用记录",
            "fields_json": [
                {"field": "overdue_count_2y", "label": "近 2 年逾期次数", "type": "select",
                 "options": ["0 次", "1-2 次", "3-5 次", "5 次以上"], "weight": 25},
                {"field": "current_overdue", "label": "当前是否有逾期", "type": "switch", "weight": 30},
            ],
        },
        {
            "step_no": 5, "step_title": "贷款用途", "step_subtitle": "本次申请的用途",
            "step_label": "贷款用途",
            "fields_json": [
                {"field": "loan_purpose", "label": "贷款用途", "type": "select",
                 "options": ["装修", "教育", "医疗", "消费", "经营", "其他"], "weight": 5},
                {"field": "loan_amount", "label": "申请金额(万元)", "type": "number", "weight": 5},
                {"field": "loan_term", "label": "申请期限(月)", "type": "select",
                 "options": ["12", "24", "36", "48", "60"], "weight": 5},
            ],
        },
    ]
    return ok({
        "bank_code": bank["code"] if isinstance(bank, dict) else bank.code,
        "bank_name": bank["name"] if isinstance(bank, dict) else bank.name,
        "total_steps": len(steps),
        "steps": steps,
    })


@router.get("/{code}/products", summary="银行推荐产品")
async def get_bank_products(
    code: str,
    user_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        bank = await _find_bank(code, db)
        stmt = (
            select(BankProduct)
            .where(BankProduct.bank_id == bank.id, BankProduct.enabled == 1)
            .order_by(BankProduct.sort_order, BankProduct.id)
        )
        res = await db.execute(stmt)
        rows = res.scalars().all()
        items = [_product_to_dict(p) for p in rows]
    except NotFoundException:
        raise
    except Exception as e:
        logger.warning(f"[banks/{code}/products] DB 查询失败，使用静态 fallback: {e}")
        # 静态 fallback：每个银行 1-2 款产品
        items = [
            {
                "id": 1, "name": f"{code} 信用贷", "subtitle": "纯信用 · 无抵押",
                "limit_min": 1, "limit_max": 50, "rate_min": 3.5, "rate_max": 7.2,
                "pass_score_min": 60, "pass_score_max": 100,
                "features": ["纯信用", "线上申请", "快速审批"],
                "requirement": "年龄 22-55，征信良好，月收入 5000+",
                "recommend": True,
            }
        ]
    bank_name = code.upper()
    return ok({
        "bank_code": code.upper(),
        "bank_name": bank_name,
        "total": len(items),
        "items": items,
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
        "limit_min": p.limit_min,
        "limit_max": p.limit_max,
        "rate_min": p.rate_min,
        "rate_max": p.rate_max,
        "pass_score_min": p.pass_score_min,
        "pass_score_max": p.pass_score_max,
        "features": p.features or [],
        "requirement": p.requirement,
        "recommend": bool(p.recommend),
    }
