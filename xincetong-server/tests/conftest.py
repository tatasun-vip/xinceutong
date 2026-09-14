"""
pytest 公共 fixtures
"""
import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


# ============================================================================
# 阶段 2 评分卡测试 fixtures
# ============================================================================


# 与 scripts/init_scorecard.py SCORECARD_SEED 同步的内存版规则
SAMPLE_RULES: list[dict] = [
    # (category, variable, option_label, score, type, is_veto)
    ("基础", "age", "22-30岁", 8, "personal", 0),
    ("基础", "age", "31-40岁", 10, "personal", 0),
    ("基础", "age", "41-50岁", 6, "personal", 0),
    ("基础", "age", "51-55岁", 3, "personal", 0),
    ("基础", "age", "18岁以下", 0, "personal", 1),
    ("基础", "age", "55岁以上", 0, "personal", 1),
    ("基础", "education", "本科及以上", 4, "personal", 0),
    ("基础", "education", "大专", 3, "personal", 0),
    ("基础", "education", "高中/中专", 1, "personal", 0),
    ("基础", "education", "初中及以下", 0, "personal", 0),
    ("基础", "marriage", "已婚有子女", 3, "personal", 0),
    ("基础", "marriage", "已婚无子女", 2, "personal", 0),
    ("基础", "marriage", "未婚", 1, "personal", 0),
    ("基础", "marriage", "离异", 0, "personal", 0),
    ("基础", "city_tier", "一线城市", 3, "personal", 0),
    ("基础", "city_tier", "新一线/省会", 2, "personal", 0),
    ("基础", "city_tier", "其他城市", 1, "personal", 0),
    ("职业", "company_type", "公务员/事业单位", 15, "personal", 0),
    ("职业", "company_type", "国企/央企", 13, "personal", 0),
    ("职业", "company_type", "上市公司", 10, "personal", 0),
    ("职业", "company_type", "民营/外企", 6, "personal", 0),
    ("职业", "company_type", "个体户/小微企业", 3, "personal", 0),
    ("职业", "company_type", "自由职业", 1, "personal", 0),
    ("职业", "work_years", "5年以上", 10, "personal", 0),
    ("职业", "work_years", "3-5年", 7, "personal", 0),
    ("职业", "work_years", "1-3年", 4, "personal", 0),
    ("职业", "work_years", "1年以下", 1, "personal", 0),
    ("职业", "social_security", "连续3年以上", 8, "personal", 0),
    ("职业", "social_security", "连续1-3年", 5, "personal", 0),
    ("职业", "social_security", "1年以下", 2, "personal", 0),
    ("职业", "social_security", "无", 0, "personal", 0),
    ("职业", "housing_fund", "高基数", 8, "personal", 0),
    ("职业", "housing_fund", "正常基数", 5, "personal", 0),
    ("职业", "housing_fund", "最低基数", 2, "personal", 0),
    ("职业", "housing_fund", "无", 0, "personal", 0),
    ("职业", "payroll", "是", 6, "personal", 0),
    ("职业", "payroll", "否", 0, "personal", 0),
    ("收入", "monthly_income", "5万以上", 30, "personal", 0),
    ("收入", "monthly_income", "3万-5万", 22, "personal", 0),
    ("收入", "monthly_income", "1.5万-3万", 15, "personal", 0),
    ("收入", "monthly_income", "8000-1.5万", 8, "personal", 0),
    ("收入", "monthly_income", "5000-8000", 3, "personal", 0),
    ("收入", "monthly_income", "5000以下", 0, "personal", 0),
    ("资产", "house", "无按揭", 18, "personal", 0),
    ("资产", "house", "有按揭", 8, "personal", 0),
    ("资产", "house", "无房", 0, "personal", 0),
    ("资产", "car", "30万以上", 10, "personal", 0),
    ("资产", "car", "10-30万", 6, "personal", 0),
    ("资产", "car", "10万以下", 2, "personal", 0),
    ("资产", "car", "无车", 0, "personal", 0),
    ("资产", "deposit", "50万以上", 8, "personal", 0),
    ("资产", "deposit", "10-50万", 5, "personal", 0),
    ("资产", "deposit", "10万以下", 2, "personal", 0),
    ("资产", "deposit", "无", 0, "personal", 0),
    ("资产", "insurance", "有", 4, "personal", 0),
    ("资产", "insurance", "无", 0, "personal", 0),
    ("征信", "credit_card_count", "无", 4, "personal", 0),
    ("征信", "credit_card_count", "1-3张", 6, "personal", 0),
    ("征信", "credit_card_count", "3-5张", 4, "personal", 0),
    ("征信", "credit_card_count", "5张以上", 1, "personal", 0),
    ("征信", "credit_card_usage", "30%以下", 8, "personal", 0),
    ("征信", "credit_card_usage", "30%-50%", 6, "personal", 0),
    ("征信", "credit_card_usage", "50%-80%", 3, "personal", 0),
    ("征信", "credit_card_usage", "80%以上", 0, "personal", 0),
    ("征信", "loan_count", "无", 6, "personal", 0),
    ("征信", "loan_count", "1-2笔", 4, "personal", 0),
    ("征信", "loan_count", "3-5笔", 1, "personal", 0),
    ("征信", "loan_count", "5笔以上", 0, "personal", 0),
    ("征信", "recent_3month_queries", "0-2次", 5, "personal", 0),
    ("征信", "recent_3month_queries", "3-5次", 2, "personal", 0),
    ("征信", "recent_3month_queries", "6次以上", 0, "personal", 0),
    ("征信", "overdue_2year", "0次", 10, "personal", 0),
    ("征信", "overdue_2year", "1-3次", 4, "personal", 0),
    ("征信", "overdue_2year", "3次以上", 0, "personal", 0),
    ("征信", "current_overdue", "有", 0, "personal", 1),
    ("征信", "current_overdue", "无", 0, "personal", 0),
    ("征信", "serial_overdue", "有", 0, "personal", 1),
    ("征信", "serial_overdue", "无", 0, "personal", 0),
    ("征信", "white_account", "是", 0, "personal", 0),
    ("征信", "white_account", "否", 0, "personal", 0),
    ("征信", "bad_status", "有", 0, "personal", 1),
    ("征信", "bad_status", "无", 0, "personal", 0),
]


def _rules_to_dicts(rules: list[tuple]) -> list[dict]:
    return [
        {
            "category": r[0],
            "variable": r[1],
            "option_label": r[2],
            "score": float(r[3]),
            "type": r[4],
            "is_veto": r[5],
            "sort_order": 0,
            "enabled": 1,
        }
        for r in rules
    ]


@pytest.fixture
def sample_rules() -> list[dict]:
    """内存版评分卡规则（与 init_scorecard.py 同步）"""
    return _rules_to_dicts(SAMPLE_RULES)


# 优秀客户画像（用于高分测试）
GOOD_PROFILE = {
    "age": "31-40岁",
    "education": "本科及以上",
    "marriage": "已婚有子女",
    "city_tier": "一线城市",
    "company_type": "公务员/事业单位",
    "work_years": "5年以上",
    "social_security": "连续3年以上",
    "housing_fund": "高基数",
    "payroll": "是",
    "monthly_income": "5万以上",
    "house": "无按揭",
    "car": "30万以上",
    "deposit": "50万以上",
    "insurance": "有",
    "credit_card_count": "1-3张",
    "credit_card_usage": "30%以下",
    "loan_count": "无",
    "recent_3month_queries": "0-2次",
    "overdue_2year": "0次",
    "current_overdue": "无",
    "serial_overdue": "无",
    "white_account": "否",
    "bad_status": "无",
}


# 极差客户画像（用于 E 级测试）
BAD_PROFILE = {
    "age": "31-40岁",
    "education": "初中及以下",
    "marriage": "离异",
    "city_tier": "其他城市",
    "company_type": "自由职业",
    "work_years": "1年以下",
    "social_security": "无",
    "housing_fund": "无",
    "payroll": "否",
    "monthly_income": "5000以下",
    "house": "无房",
    "car": "无车",
    "deposit": "无",
    "insurance": "无",
    "credit_card_count": "5张以上",
    "credit_card_usage": "80%以上",
    "loan_count": "5笔以上",
    "recent_3month_queries": "6次以上",
    "overdue_2year": "3次以上",
    "current_overdue": "无",
    "serial_overdue": "无",
    "white_account": "否",
    "bad_status": "无",
}
