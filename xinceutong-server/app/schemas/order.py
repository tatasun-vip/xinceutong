"""
订单 / 支付相关 Pydantic 模型
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderCreateRequest(BaseModel):
    """创建订单请求"""

    assessment_id: int
    promoter_code: str | None = None


class OrderCreateResponse(BaseModel):
    """创建订单响应（含微信支付参数）"""

    order_no: str
    amount: Decimal
    jsapi_params: dict | None = None
