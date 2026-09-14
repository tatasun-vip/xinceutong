"""
推广员相关 Pydantic 模型
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PromoterApplyRequest(BaseModel):
    """推广员入驻申请"""

    real_name: str = Field(..., max_length=64)
    id_card: str = Field(..., max_length=32, description="身份证号，仅入库前加密")
    org_name: str | None = None
    city: str | None = None
    years: int = 0


class PromoterPriceUpdate(BaseModel):
    """推广员调价"""

    custom_price: Decimal = Field(..., ge=Decimal("6.99"), le=Decimal("19.99"))


class PromoterDashboardResponse(BaseModel):
    """工作台数据"""

    total_earnings: Decimal
    balance: Decimal
    today_clicks: int
    today_assessments: int
    today_payments: int
    total_clicks: int
    total_payments: int
    pending_withdraw: Decimal
