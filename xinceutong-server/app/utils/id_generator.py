"""
统一 ID / 单号生成器
- report_no: R + YYYYMMDD + 4 位随机
- order_no:  O + YYYYMMDDHHmmss + 6 位随机
- share_code: 6 位大写字母+数字（去除易混字符 0/O/1/I）
- promoter_code: 6 位（推广员推广码）
"""
import random
import string
from datetime import datetime


_REPORT_RANDOM = string.ascii_uppercase + string.digits
_ORDER_RANDOM = string.digits
# 推广码 / 分享码字符集，去除易混的 0/O/1/I/L
_SAFE_CHARS = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def _now(fmt: str) -> str:
    return datetime.now().strftime(fmt)


def gen_report_no() -> str:
    """报告编号：R20260910XXXX"""
    return "R" + _now("%Y%m%d") + "".join(random.choices(_REPORT_RANDOM, k=4))


def gen_order_no() -> str:
    """订单号：O20260910153000123456"""
    return "O" + _now("%Y%m%d%H%M%S") + "".join(random.choices(_ORDER_RANDOM, k=6))


def gen_share_code(length: int = 6) -> str:
    """分享码：6 位（无易混字符）"""
    return "".join(random.choices(_SAFE_CHARS, k=length))


def gen_promoter_code(length: int = 6) -> str:
    """推广员推广码：6 位"""
    return "".join(random.choices(_SAFE_CHARS, k=length))
