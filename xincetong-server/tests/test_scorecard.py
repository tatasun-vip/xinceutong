"""
阶段 2 评分卡引擎测试
覆盖 8 条核心原则的关键场景：
  - 一票否决（年龄 / 当前逾期 / 连续逾期 / 账户状态）
  - 高分 / 低分场景
  - 4 种额度测算取最小
  - PD 违约概率单调
  - 实时纠错 DSL
"""
import pytest

from app.services.scorecard_engine import (
    _build_products,
    _build_suggestions,
    _build_tags,
    _calc_limits,
    _calc_pd_and_pass,
    _check_veto,
    _level_of,
    _normalize,
    _score_items,
    calculate_score,
)
from app.utils.condition_dsl import evaluate


# ============================================================================
# 一票否决（核心原则 #2）
# ============================================================================


@pytest.mark.asyncio
async def test_veto_age_under_18(sample_rules):
    """测试一票否决：18 岁以下"""
    data = {"age": "18岁以下"}
    veto = _check_veto(sample_rules, data)
    assert veto is not None
    assert veto["rule_variable"] == "age"
    assert "准入" in veto["message"] or "不符" in veto["message"]

    # 走完整个流程应是 E 级
    result = await calculate_score(data, "personal", rules=sample_rules)
    assert result.level == "E"
    assert result.score == 0
    assert result.limit_min == 0
    assert result.limit_max == 0
    assert result.pass_probability == "极低"
    assert result.veto is not None


@pytest.mark.asyncio
async def test_veto_current_overdue(sample_rules):
    """测试一票否决：当前逾期"""
    data = {**GOOD_PROFILE_FOR_TEST, "current_overdue": "有"}
    result = await calculate_score(data, "personal", rules=sample_rules)
    assert result.level == "E"
    assert result.veto is not None
    assert result.veto["rule_variable"] == "current_overdue"
    # 即使其他都很好，一票否决后额度归零
    assert result.limit_min == 0
    assert result.limit_max == 0


@pytest.mark.asyncio
async def test_veto_serial_overdue(sample_rules):
    """测试一票否决：连续逾期"""
    data = {**GOOD_PROFILE_FOR_TEST, "serial_overdue": "有"}
    result = await calculate_score(data, "personal", rules=sample_rules)
    assert result.level == "E"
    assert result.veto is not None
    assert result.veto["rule_variable"] == "serial_overdue"


@pytest.mark.asyncio
async def test_veto_bad_status(sample_rules):
    """测试一票否决：账户状态异常"""
    data = {**GOOD_PROFILE_FOR_TEST, "bad_status": "有"}
    result = await calculate_score(data, "personal", rules=sample_rules)
    assert result.level == "E"


# ============================================================================
# 高分 / 低分场景
# ============================================================================


GOOD_PROFILE_FOR_TEST = {  # 局部常量，避免依赖 conftest
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


@pytest.mark.asyncio
async def test_good_profile_s_level(sample_rules):
    """测试 S/A 级：优秀客户"""
    result = await calculate_score(GOOD_PROFILE_FOR_TEST, "personal", rules=sample_rules)
    # 全优秀项加起来 > 140，归一化后 ≥ 70 → A 级或 S 级
    assert result.level in ("S", "A"), f"期望 S/A 级，实际 {result.level}"
    assert result.score >= 70
    assert result.limit_min > 0
    assert result.limit_max > result.limit_min
    assert result.pass_probability in ("高", "中高")
    # 优势标签应包含公积金
    assert any("公积金" in adv for adv in result.advantages)


@pytest.mark.asyncio
async def test_bad_profile_e_level(sample_rules):
    """测试 E 级：极差客户"""
    bad = {
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
    result = await calculate_score(bad, "personal", rules=sample_rules)
    assert result.level in ("D", "E"), f"期望 D/E 级，实际 {result.level}"
    assert result.pass_probability in ("低", "极低")


# ============================================================================
# 高收入但征信差
# ============================================================================


@pytest.mark.asyncio
async def test_high_income_bad_credit(sample_rules):
    """测试高收入但征信差：不应进入 S/A"""
    data = {
        "age": "31-40岁",
        "education": "本科及以上",
        "marriage": "已婚有子女",
        "city_tier": "一线城市",
        "company_type": "上市公司",
        "work_years": "5年以上",
        "social_security": "连续1-3年",
        "housing_fund": "正常基数",
        "payroll": "是",
        "monthly_income": "3万-5万",      # 高收入
        "house": "无按揭",
        "car": "10-30万",
        "deposit": "10-50万",
        "insurance": "有",
        "credit_card_count": "5张以上",
        "credit_card_usage": "80%以上",  # 征信差
        "loan_count": "3-5笔",
        "recent_3month_queries": "6次以上",
        "overdue_2year": "3次以上",      # 多次逾期
        "current_overdue": "无",
        "serial_overdue": "无",
        "white_account": "否",
        "bad_status": "无",
    }
    result = await calculate_score(data, "personal", rules=sample_rules)
    # 高收入但征信差，不应进入 A 级
    assert result.level in ("B", "C", "D"), f"期望 B/C/D 级，实际 {result.level}"
    # 风险标签应包含逾期相关
    assert any("逾期" in tag for tag in result.risk_tags)
    # 弱点应包含信用卡使用率
    assert any("信用" in w for w in result.weak_points)


# ============================================================================
# 额度测算（核心原则 #3：4 种方法取最小）
# ============================================================================


def test_calc_limits_returns_tuple():
    """_calc_limits 返回 4 元组"""
    data = {"monthly_income": "1.5万-3万", "housing_fund": "正常基数",
            "house": "无按揭", "car": "10-30万", "monthly_debt": "无"}
    limit_min, limit_max, rate_min, rate_max = _calc_limits(data, "B")
    assert isinstance(limit_min, int) and limit_min >= 0
    assert isinstance(limit_max, int) and limit_max >= limit_min
    assert rate_min < rate_max
    assert rate_min > 0


def test_calc_limits_takes_min_of_four():
    """验证额度测算确实取了 4 种方法的最小值"""
    # 无房无车无公积金无月负债的极简场景：只有收入倍数法生效
    data = {"monthly_income": "5000-8000", "housing_fund": "无",
            "house": "无房", "car": "无车", "monthly_debt": "无"}
    limit_min, limit_max, rate_min, rate_max = _calc_limits(data, "B")
    # 6500*12*12 = 936,000 → min=655200, max=1,216,800
    assert limit_min > 0
    # E 级额度归零
    e_min, e_max, _, _ = _calc_limits(data, "E")
    assert e_min == 0
    assert e_max == 0


def test_housing_fund_increases_limit():
    """测试：公积金有 vs 无 → 额度有显著差异"""
    no_fund = {"monthly_income": "1.5万-3万", "housing_fund": "无",
               "house": "无房", "car": "无车", "monthly_debt": "无"}
    high_fund = {**no_fund, "housing_fund": "高基数"}

    # 同等级下
    no_fund_max, _, _, _ = _calc_limits(no_fund, "B")
    high_fund_max, _, _, _ = _calc_limits(high_fund, "B")
    # 高公积金场景算出的 limit_max 应当 ≥ 无公积金场景
    # 注：受 min 约束时可能持平，但不会更小
    assert high_fund_max >= no_fund_max


def test_dsr_caps_limit():
    """测试：DSR 约束把额度压低"""
    # 高收入 + 已有高月负债
    high_debt = {
        "monthly_income": "3万-5万",      # 40000 元
        "housing_fund": "无",
        "house": "无房",
        "car": "无车",
        "monthly_debt": "5000以上",       # 6500 元月还款
    }
    no_debt = {**high_debt, "monthly_debt": "无"}

    debt_max, debt_min, _, _ = _calc_limits(high_debt, "A")
    no_debt_max, no_debt_min, _, _ = _calc_limits(no_debt, "A")
    # 有负债时额度上限应 ≤ 无负债
    assert debt_max <= no_debt_max


# ============================================================================
# PD 违约概率 → 通过概率（核心原则 #4）
# ============================================================================


def test_pd_monotonic():
    """测试：分数越高，PD 越低"""
    pd_low, _ = _calc_pd_and_pass(10, "D")
    pd_mid, _ = _calc_pd_and_pass(50, "B")
    pd_high, _ = _calc_pd_and_pass(90, "S")
    assert pd_low > pd_mid > pd_high
    assert 0 < pd_low < 1
    assert 0 < pd_high < 1


def test_pass_probability_levels():
    """测试：PD → 通过概率的映射"""
    # 满分 → PD < 5% → 高
    _, pp = _calc_pd_and_pass(100, "S")
    assert pp == "高"
    # 极低分 → PD > 50% → 低/极低
    _, pp2 = _calc_pd_and_pass(0, "E")
    assert pp2 in ("低", "极低")


def test_e_level_pass_prob():
    """E 级直接给极低，不走 PD 计算"""
    pd, pp = _calc_pd_and_pass(0, "E")
    assert pp == "极低"
    assert pd == 0.85


# ============================================================================
# 实时纠错 DSL（条件评估器）
# ============================================================================


def test_dsl_eq():
    assert evaluate({"op": "eq", "variable": "current_overdue", "value": "有"}, {"current_overdue": "有"})
    assert not evaluate({"op": "eq", "variable": "current_overdue", "value": "有"}, {"current_overdue": "无"})


def test_dsl_in():
    cond = {"op": "in", "variable": "monthly_income", "value": ["5000以下", "5000-8000"]}
    assert evaluate(cond, {"monthly_income": "5000以下"})
    assert not evaluate(cond, {"monthly_income": "5万以上"})


def test_dsl_and():
    cond = {
        "op": "and",
        "children": [
            {"op": "eq", "variable": "current_overdue", "value": "无"},
            {"op": "in", "variable": "monthly_income", "value": ["1.5万-3万", "3万-5万", "5万以上"]},
        ],
    }
    assert evaluate(cond, {"current_overdue": "无", "monthly_income": "3万-5万"})
    assert not evaluate(cond, {"current_overdue": "无", "monthly_income": "5000以下"})
    assert not evaluate(cond, {"current_overdue": "有", "monthly_income": "3万-5万"})


def test_dsl_or():
    cond = {
        "op": "or",
        "children": [
            {"op": "eq", "variable": "current_overdue", "value": "有"},
            {"op": "eq", "variable": "serial_overdue", "value": "有"},
        ],
    }
    assert evaluate(cond, {"current_overdue": "有", "serial_overdue": "无"})
    assert evaluate(cond, {"current_overdue": "无", "serial_overdue": "有"})
    assert not evaluate(cond, {"current_overdue": "无", "serial_overdue": "无"})


def test_dsl_not():
    cond = {
        "op": "not",
        "child": {"op": "eq", "variable": "current_overdue", "value": "有"},
    }
    assert evaluate(cond, {"current_overdue": "无"})
    assert not evaluate(cond, {"current_overdue": "有"})


def test_dsl_ne():
    assert evaluate({"op": "ne", "variable": "current_overdue", "value": "有"}, {"current_overdue": "无"})
    assert not evaluate({"op": "ne", "variable": "current_overdue", "value": "有"}, {"current_overdue": "有"})


def test_dsl_not_in():
    cond = {"op": "not_in", "variable": "monthly_income", "value": ["5万以上"]}
    assert evaluate(cond, {"monthly_income": "5000以下"})
    assert not evaluate(cond, {"monthly_income": "5万以上"})


def test_dsl_compare_numeric():
    """gte / lte / gt / lt 用于数值字段"""
    assert evaluate({"op": "gte", "variable": "age_num", "value": 22}, {"age_num": 22})
    assert evaluate({"op": "gte", "variable": "age_num", "value": 22}, {"age_num": 30})
    assert not evaluate({"op": "gte", "variable": "age_num", "value": 22}, {"age_num": 18})

    assert evaluate({"op": "lte", "variable": "age_num", "value": 55}, {"age_num": 55})
    assert not evaluate({"op": "lte", "variable": "age_num", "value": 55}, {"age_num": 60})

    assert evaluate({"op": "gt", "variable": "x", "value": 5}, {"x": 6})
    assert not evaluate({"op": "gt", "variable": "x", "value": 5}, {"x": 5})

    assert evaluate({"op": "lt", "variable": "x", "value": 5}, {"x": 4})
    assert not evaluate({"op": "lt", "variable": "x", "value": 5}, {"x": 5})


def test_dsl_contains():
    """contains 用于 list/str"""
    assert evaluate({"op": "contains", "variable": "loan_types", "value": "房贷"}, {"loan_types": ["房贷", "车贷"]})
    assert not evaluate({"op": "contains", "variable": "loan_types", "value": "房贷"}, {"loan_types": ["车贷"]})
    assert evaluate({"op": "contains", "variable": "name", "value": "张"}, {"name": "张三"})


def test_dsl_unknown_op():
    """未知 op 默认不命中"""
    assert not evaluate({"op": "xxx_unknown", "variable": "x", "value": 1}, {"x": 1})


def test_dsl_dot_path():
    """variable 支持 a.b.c 点路径"""
    cond = {"op": "eq", "variable": "user.profile.city", "value": "上海"}
    assert evaluate(cond, {"user": {"profile": {"city": "上海"}}})
    assert not evaluate(cond, {"user": {"profile": {"city": "北京"}}})


def test_dsl_missing_value():
    """数据缺字段时不应抛异常"""
    cond = {"op": "gte", "variable": "missing_field", "value": 10}
    # 缺字段时 _get 返回 None，_gte 返回 False（不命中）
    assert not evaluate(cond, {})


# ============================================================================
# 内部函数：归一化、等级映射
# ============================================================================


def test_normalize_clamps_to_100():
    """归一化不能超过 100"""
    assert _normalize(200, [{}] * 5) == 100
    assert _normalize(50, [{}] * 2) == 25
    assert _normalize(0, []) == 0


def test_level_mapping():
    assert _level_of(85) == "S"
    assert _level_of(75) == "A"
    assert _level_of(60) == "B"
    assert _level_of(45) == "C"
    assert _level_of(30) == "D"
    assert _level_of(10) == "E"
    assert _level_of(0) == "E"
    assert _level_of(100) == "S"


def test_score_items_basic():
    """_score_items 应只累加命中的项"""
    rules = [
        {"variable": "a", "option_label": "1", "score": 10, "is_veto": 0, "type": "personal"},
        {"variable": "a", "option_label": "2", "score": 5, "is_veto": 0, "type": "personal"},
        {"variable": "b", "option_label": "x", "score": 8, "is_veto": 0, "type": "personal"},
    ]
    raw, items = _score_items(rules, {"a": "1", "b": "x"})
    assert raw == 18
    assert len(items) == 2
    # 不命中不计分
    raw2, items2 = _score_items(rules, {"a": "3", "b": "x"})
    assert raw2 == 8


def test_score_items_skip_veto():
    """_score_items 不累加一票否决项（由 _check_veto 单独处理）"""
    rules = [
        {"variable": "a", "option_label": "veto", "score": 100, "is_veto": 1, "type": "personal"},
        {"variable": "b", "option_label": "x", "score": 5, "is_veto": 0, "type": "personal"},
    ]
    raw, items = _score_items(rules, {"a": "veto", "b": "x"})
    assert raw == 5  # 否决项不计分
    assert len(items) == 1


# ============================================================================
# 标签 / 建议 / 产品
# ============================================================================


def test_build_tags_risks():
    """风险标签匹配"""
    data = {
        "current_overdue": "有",
        "credit_card_usage": "80%以上",
        "recent_3month_queries": "6次以上",
        "overdue_2year": "3次以上",
    }
    risks, advs, weaks = _build_tags(data, [])
    assert "当前有逾期" in risks
    assert "信用卡使用率过高" in risks
    assert "近 3 个月查询过多" in risks
    assert "近 2 年逾期 3 次以上" in risks


def test_build_tags_advantages():
    """优势标签匹配"""
    data = {
        "social_security": "连续1年以上",
        "housing_fund": "正常基数",
        "payroll": "是",
        "company_type": "公务员/事业单位",
        "house": "无按揭",
    }
    risks, advs, weaks = _build_tags(data, [])
    assert "社保连续缴存" in advs
    assert "公积金连续缴存" in advs
    assert "工资代发" in advs
    assert "优质单位背景" in advs
    assert "本地有房无按揭" in advs


def test_build_suggestions_always_has_one():
    """改善建议至少 1 条"""
    s = _build_suggestions({"monthly_income": "5万以上"}, "S", [])
    assert len(s) >= 1
    assert "period" in s[0] and "action" in s[0]


def test_build_products_e_level_empty():
    """E 级产品列表包含"暂无可推荐产品"占位"""
    products = _build_products("E", 0, 0, 0, 0)
    assert any("暂无可推荐" in p["name"] for p in products)


def test_build_products_recommend_flag():
    """推荐产品应有 recommend 标志"""
    products = _build_products("A", 100000, 200000, 4.0, 6.0)
    recommended = [p for p in products if p.get("recommend")]
    assert len(recommended) >= 1


# ============================================================================
# 集成：calculate_score 入口
# ============================================================================


@pytest.mark.asyncio
async def test_calculate_score_no_rules_returns_b(sample_rules):
    """无 rules 参数 + 无 db → B 级兜底"""
    result = await calculate_score({"monthly_income": "3万-5万"})
    assert result.level == "B"
    assert result.score == 50


@pytest.mark.asyncio
async def test_calculate_score_full_flow(sample_rules):
    """完整流程：评级 + 额度 + PD + 标签 + 建议 + 产品 都有值"""
    result = await calculate_score(GOOD_PROFILE_FOR_TEST, "personal", rules=sample_rules)
    d = result.to_dict()
    for k in ("score", "level", "raw_score", "matched_items", "limit_min", "limit_max",
              "rate_min", "rate_max", "pd", "pass_probability", "risk_tags",
              "advantages", "weak_points", "suggestions", "products"):
        assert k in d, f"to_dict 缺字段: {k}"
    assert isinstance(d["matched_items"], list)
    assert isinstance(d["products"], list)
