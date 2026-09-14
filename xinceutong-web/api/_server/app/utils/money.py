"""
金额 / 利率工具
所有内部计算以"分"为单位整数化，DB 字段用 INT 或 DECIMAL
"""
from typing import Iterable


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
    return INCOME_MIDPOINT.get(label, 0)


def housing_fund_value(label: str) -> int:
    return HOUSING_FUND_MIDPOINT.get(label, 0)


def house_value(label: str) -> int:
    return HOUSE_VALUE.get(label, 0)


def car_value(label: str) -> int:
    return CAR_VALUE.get(label, 0)


def credit_usage_ratio(label: str) -> float:
    return CREDIT_USAGE_MIDPOINT.get(label, 0.0)


def monthly_debt_value(label: str) -> int:
    return MONTHLY_DEBT.get(label, 0)


def min_of(values: Iterable[int | float]) -> int:
    """取最小值（过滤掉 0/None/负数）"""
    nums = [v for v in values if v and v > 0]
    return min(nums) if nums else 0
