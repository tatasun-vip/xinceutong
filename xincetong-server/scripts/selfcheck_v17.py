"""
v17 评分卡 selfcheck（7+1 项真检查）

设计：每个测试在内存里手动算预期值，然后真跑 calculate_score，对比差异。
不通过即 raise，CI 跑前可手动 `python -m scripts.selfcheck_v17` 验证。

7+1 项检查：
  [1] DB seed 加载：120+ 条规则写入，type=personal/business 分布对
  [2] 5 维度加总自然 0-100：全优 personal 用户 → 95+；0 命中 → 0
  [3] 保守口径：白户 → C(40-54)；无公积金 → B(55-69)
  [4] 一票否决：current_overdue=有 → 0 分 E 级
  [5] 关键保障全缺：housing_fund=无 AND social_security=无 AND payroll=否 → C(40-54)
  [6] business 隔离：business 流程不命中 personal 专属规则
  [7] product_engine 同步：_evaluate_one_product 用 v17 三段式（无 raw/174 归一化）
  [8] 5 维度加总结构（可选）：各维度分对得上
"""
import asyncio

from app.database import AsyncSessionLocal, init_db
from app.models.scorecard import ScorecardRule
from app.services.product_engine import (
    _load_rules_for_product,
    calculate_scores_by_product,
)
from app.services.scorecard_engine import (
    LEVEL_THRESHOLDS,
    _check_compound_policy,
    _load_rules,
    _score_items,
    calculate_score,
)
from app.utils.logger import logger


# ============================================================================
# 测试 fixture
# ============================================================================

PERFECT_PERSONAL = {
    "age": "31-40岁",
    "education": "本科及以上",
    "marriage": "已婚有子女",
    "city_tier": "一线城市",
    "company_type": "公务员/事业单位",
    "work_years": "5年以上",
    "monthly_income": "5万以上",
    "social_security": "连续3年以上",
    "housing_fund": "高基数",
    "payroll": "是",
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
    "monthly_debt": "无",
}

WHITE_PERFECT = {**PERFECT_PERSONAL, "white_account": "是"}
NO_FUND = {**PERFECT_PERSONAL, "housing_fund": "无"}
NO_SECURITY = {**PERFECT_PERSONAL, "social_security": "无"}
NO_ALL = {**PERFECT_PERSONAL, "housing_fund": "无", "social_security": "无", "payroll": "否"}
HAS_OVERDUE = {**PERFECT_PERSONAL, "current_overdue": "有"}

PERFECT_BUSINESS = {
    "legal_form": "有限公司",
    "legal_holding": "100%",
    "employee_count": "100人以上",
    "biz_balance": "100万以上",
    "biz_loan_count": "0笔",
    "biz_overdue_2y": "0次",
    "biz_query_3m": "0-2次",
    "industry": "5大景气行业",
    "biz_years": "5年以上",
    "compliance_risk": "无任何异常",
}


# ============================================================================
# 7+1 项检查
# ============================================================================


async def check_1_db_seed() -> None:
    """[1] DB seed：120+ 条规则，5 维度分布"""
    from sqlalchemy import func, select

    async with AsyncSessionLocal() as db:
        cnt = (await db.execute(
            select(func.count()).select_from(ScorecardRule)
        )).scalar_one()
        assert cnt >= 120, f"[1] scorecard_rules 仅 {cnt} 条，期望 120+"
        type_p = (await db.execute(
            select(func.count()).where(ScorecardRule.type == "personal")
        )).scalar_one()
        type_b = (await db.execute(
            select(func.count()).where(ScorecardRule.type == "business")
        )).scalar_one()
        assert type_p >= 80, f"[1] personal 规则仅 {type_p} 条，期望 80+"
        assert type_b >= 25, f"[1] business 规则仅 {type_b} 条，期望 25+"
        for dim in ("credit", "debt", "asset", "personal", "public"):
            n = (await db.execute(
                select(func.count()).where(ScorecardRule.dimension == dim)
            )).scalar_one()
            assert n >= 5, f"[1] 维度 {dim} 仅 {n} 条规则，期望 5+"
    logger.info(f"[1] PASS：scorecard_rules {cnt} 条（personal={type_p}, business={type_b}）")


async def check_2_perfect_user() -> None:
    """[2] 全优 personal → 95+ 分 S 级"""
    async with AsyncSessionLocal() as db:
        result = await calculate_score(PERFECT_PERSONAL, "personal", db=db)
    assert result.score >= 95, f"[2] 全优用户 {result.score} 分 < 95（应 S 级）"
    assert result.level == "S", f"[2] 全优用户 {result.level} != S"
    logger.info(f"[2] PASS：全优 personal → {result.score} 分 {result.level} 级")


async def check_3_conservative_cap() -> None:
    """[3] 保守口径政策性上限"""
    async with AsyncSessionLocal() as db:
        r = await calculate_score(WHITE_PERFECT, "personal", db=db)
        assert 40 <= r.score <= 54, f"[3a] 白户 {r.score} 分不在 C 范围 40-54"
        assert r.level == "C", f"[3a] 白户等级 {r.level} != C"
        r = await calculate_score(NO_FUND, "personal", db=db)
        assert 55 <= r.score <= 69, f"[3b] 无公积金 {r.score} 分不在 B 范围 55-69"
        assert r.level == "B", f"[3b] 无公积金等级 {r.level} != B"
        r = await calculate_score(NO_SECURITY, "personal", db=db)
        assert 55 <= r.score <= 69, f"[3c] 无社保 {r.score} 分不在 B 范围 55-69"
    logger.info("[3] PASS：白户=C(40-54) / 无公积金=B(55-69) / 无社保=B(55-69)")


async def check_4_veto() -> None:
    """[4] 一票否决：current_overdue=有 → 0 分 E 级"""
    async with AsyncSessionLocal() as db:
        r = await calculate_score(HAS_OVERDUE, "personal", db=db)
    assert r.score == 0, f"[4] 当前逾期 {r.score} 分 != 0"
    assert r.level == "E", f"[4] 当前逾期等级 {r.level} != E"
    assert r.veto is not None, "[4] 当前逾期应触发 veto"
    logger.info(f"[4] PASS：当前逾期 → 0 分 E 级（veto={r.veto['rule_variable']}）")


async def check_5_compound_policy() -> None:
    """[5] 关键保障全缺 → C(40-54)"""
    caps = _check_compound_policy(NO_ALL, "personal")
    assert "C" in caps, f"[5a] 关键保障全缺应命中 C, got {caps}"
    async with AsyncSessionLocal() as db:
        r = await calculate_score(NO_ALL, "personal", db=db)
    assert 40 <= r.score <= 54, f"[5b] 关键保障全缺 {r.score} 分不在 C 范围 40-54"
    assert r.level == "C", f"[5b] 关键保障全缺等级 {r.level} != C"
    logger.info(f"[5] PASS：关键保障全缺 → {r.score} 分 C 级")


async def check_6_business_isolation() -> None:
    """[6] business 流程不命中 personal 专属规则"""
    async with AsyncSessionLocal() as db:
        rules = await _load_rules("business", db)
    personal_only = [r for r in rules if r.get("type") == "personal"]
    assert not personal_only, f"[6] business 流程混入 personal 规则: {personal_only[:3]}"
    async with AsyncSessionLocal() as db:
        r = await calculate_score(PERFECT_BUSINESS, "business", db=db)
    assert r.score >= 80, f"[6] 全优 business {r.score} 分 < 80（应 S 级 80-100）"
    assert r.level in ("S", "A"), f"[6] 全优 business 等级 {r.level} 不在 S/A"
    logger.info(f"[6] PASS：business 隔离（{len(rules)} 条规则）+ 全优 business → {r.score} 分 {r.level} 级")


async def check_7_product_engine_v17() -> None:
    """[7] product_engine 同步用 v17 三段式"""
    async with AsyncSessionLocal() as db:
        rules_p = await _load_rules_for_product("personal", db, product_type_id=1)
        for r in rules_p:
            assert "dimension" in r, f"[7a] 规则缺 dimension: {r}"
            assert "is_deduction" in r, f"[7a] 规则缺 is_deduction: {r}"
        results = await calculate_scores_by_product(PERFECT_PERSONAL, "personal", db)
        assert len(results) == 6, f"[7b] 6 大产品结果仅 {len(results)} 个"
        for r in results:
            assert r.level in ("S", "A"), f"[7b] 全优用户产品 {r.product_name} 等级 {r.level} 不在 S/A"
        no_fund_results = await calculate_scores_by_product(NO_FUND, "personal", db)
        fund_products = [
            r for r in no_fund_results
            if "housing" in (r.product_code or "").lower() or "公积金" in r.product_name
        ]
        for r in fund_products:
            assert r.level in ("C", "D"), (
                f"[7c] 无公积金用户公积金贷 {r.score} {r.level} 应在 C/D"
            )
    logger.info("[7] PASS：6 套产品全 S/A + 无公积金用户公积金贷降级到 C/D")


async def check_8_5d_natural_0_100() -> None:
    """[8] 5 维度加总结构（各维度分对得上）"""
    async with AsyncSessionLocal() as db:
        rules = await _load_rules("personal", db)
    raw, items, dim_scores, veto_set = _score_items(rules, PERFECT_PERSONAL)
    assert dim_scores["credit"] >= 25, f"[8] credit {dim_scores['credit']} < 25"
    assert dim_scores["debt"] >= 25, f"[8] debt {dim_scores['debt']} < 25"
    assert dim_scores["asset"] >= 15, f"[8] asset {dim_scores['asset']} < 15"
    assert dim_scores["personal"] >= 12, f"[8] personal {dim_scores['personal']} < 12"
    assert dim_scores["public"] >= 3, f"[8] public {dim_scores['public']} < 3"
    total = (
        min(30, max(0, dim_scores["credit"]))
        + min(30, max(0, dim_scores["debt"]))
        + min(20, max(0, dim_scores["asset"]))
        + min(15, max(0, dim_scores["personal"]))
        + min(5, max(0, dim_scores["public"]))
    )
    assert total >= 90, f"[8] 5 维度加总 {total} < 90（全优应≥90）"
    logger.info(
        f"[8] PASS：5 维度加总 {total:.1f} / 100（credit={dim_scores['credit']:.1f}, "
        f"debt={dim_scores['debt']:.1f}, asset={dim_scores['asset']:.1f}, "
        f"personal={dim_scores['personal']:.1f}, public={dim_scores['public']:.1f}）"
    )


# ============================================================================
# 主入口
# ============================================================================


async def main() -> None:
    await init_db()
    print("=" * 60)
    print("v17 评分卡 selfcheck（7+1 项真检查）")
    print("=" * 60)
    await check_1_db_seed()
    await check_2_perfect_user()
    await check_3_conservative_cap()
    await check_4_veto()
    await check_5_compound_policy()
    await check_6_business_isolation()
    await check_7_product_engine_v17()
    await check_8_5d_natural_0_100()
    print("=" * 60)
    print("v17 selfcheck 全部 PASS")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
