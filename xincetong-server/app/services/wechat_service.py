"""
微信相关服务（占位，阶段 4 实现）
- code2session: jscode -> openid
- 支付下单 / 回调验签 / 退款
"""
from app.utils.logger import logger


def code2session(code: str) -> dict:
    """用 code 换 openid"""
    logger.info(f"wechat code2session: code={code[:8]}***")
    return {"openid": "", "unionid": "", "session_key": ""}


def create_jsapi_order(order_no: str, amount: int, openid: str) -> dict:
    """微信支付 JSAPI 下单，返回前端唤起支付所需的参数"""
    logger.info(f"wechat create_jsapi_order: {order_no}")
    return {}


def verify_pay_notify(payload: dict) -> bool:
    """校验微信支付回调签名"""
    return False
