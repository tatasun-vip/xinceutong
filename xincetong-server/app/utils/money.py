"""
金额 / 利率工具
所有内部计算以"分"为单位整数化，DB 字段用 INT 或 DECIMAL
v15 (2026-09-14): 5 个 value 函数加规范化
  - 旧问题：前端传 "1.5 万-3 万"（带空格），评分卡 _norm 去空格能匹配上 → score 正常；
    但 money.py 直接 dict.get 没规范化 → 查不到 → 返 0 → 额度全是 0
  - 修复：5 个 value 函数全部 norm 后再查表
v15a (2026-09-14): 导出 norm 给 product_engine / scorecard_engine 复用
  - product_engine.py 4 个内联 dict（annual_tax_map / invoice_map / tax_rate_map / mult_map）
    和 1 处字符串 == 比较（house == "无按揭"）
  - scorecard_engine.py 1 处字符串 == 比较（house_net 分支）
  - 这些位置没走 value 函数，直接 dict.get 或 == 比较会"评分对但额度 0"
"""
from typing import Iterable


def norm(s) -> str:
    """去空格、全角转半角、转小写（与 scorecard_engine._norm 逻辑一致）

    前端选项值常有空格（如 "1.5 万-3 万"），但 dict 的 key 是无空格版本（"1.5万-3万"）。
    不规范化会导致"评分有，额度是 0"的诡异 bug。

    v15a: 公开导出（去掉下划线），让 product_engine / scorecard_engine 复用
    """
    if s is None:
        return ""
    return str(s).replace(" ", "").replace("　", "").lower()


# 向后兼容：保留 _norm 名字（避免破坏 scorecard_engine 旧引用）
_norm = norm


# 月收入区间 → 收入中位数（元）
INCOME_MIDPOINT: dict[str, int] = {
    "5000以下": 4000,
    "5000-8000": 6500,
    "8000-1.5万": 11500,
    "1.5万-3万": 22500,
    "3万-5万": 40000,
    "5万以上": 60000,
}

# 月公积金基数 → 月公积金金额（元，按 12% 缴存推算）
HOUSING_FUND_MIDPOINT: dict[str, int] = {
    "无": 0,
    "最低基数": 250,
    "正常基数": 1000,
    "高基数": 3500,
}

# 房产 / 车产价值区间 → 中位数（元）
HOUSE_VALUE: dict[str, int] = {
    "无房": 0,
    "无按揭": 1_500_000,
    "有按揭": 1_500_000,
}

CAR_VALUE: dict[str, int] = {
    "无车": 0,
    "10万以下": 60_000,
    "10-30万": 200_000,
    "30万以上": 450_000,
}

# 负债 / 信用卡使用率
CREDIT_USAGE_MIDPOINT: dict[str, float] = {
    "30%以下": 0.15,
    "30%-50%": 0.40,
    "50%-80%": 0.65,
    "80%以上": 0.90,
}

# 已有月还款 → 元（用于 DSR 计算）
MONTHLY_DEBT: dict[str, int] = {
    "无": 0,
    "1000以下": 800,
    "1000-3000": 2000,
    "3000-5000": 4000,
    "5000以上": 6500,
}


def income_value(label: str) -> int:
    return INCOME_MIDPOINT.get(norm(label), 0)


def housing_fund_value(label: str) -> int:
    return HOUSING_FUND_MIDPOINT.get(norm(label), 0)


def house_value(label: str) -> int:
    return HOUSE_VALUE.get(norm(label), 0)


def car_value(label: str) -> int:
    return CAR_VALUE.get(norm(label), 0)


def credit_usage_ratio(label: str) -> float:
    return CREDIT_USAGE_MIDPOINT.get(norm(label), 0.0)


def monthly_debt_value(label: str) -> int:
    return MONTHLY_DEBT.get(norm(label), 0)


def min_of(values: Iterable[int | float]) -> int:
    """取最小值（过滤掉 0/None/负数）"""
    nums = [v for v in values if v and v > 0]
    return min(nums) if nums else 0
