"""
分佣计算（占位，阶段 6 实现）
订单支付成功后调用：
- base_commission = base_price * commission_rate
- markup_commission = markup * commission_rate
- platform_income = amount - base_commission - markup_commission
- 事务：写 commissions + 更新 promoters.balance
"""
from app.utils.logger import logger


def settle_commission(order_id: int) -> dict:
    """结算一笔订单的分佣"""
    logger.info(f"settle_commission: order_id={order_id}")
    return {"ok": False, "reason": "TODO"}
