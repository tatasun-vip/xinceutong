"""
补全 business 类型评分卡规则（v5 P0）

背景：
  v4 仅有 7 个企业变量（纳税/开票/行业），bank 模型实际做对公贷款还需要：
  1. 企业征信（对公贷款笔数 / 逾期 / 查询）
  2. 合规风险（经营异常 / 行政处罚 / 司法风险 / 失信被执行人）
  3. 企业真实经营（参保人数 / 对公账户日均余额）
  4. 法人画像（组织形式 / 持股比例）

v5 升级（8 新变量 + 4 维度加权 + 一票否决）：
  法人画像（30% 权重 = 18 分满分）：
    - legal_form       组织形式（5 档）
    - legal_holding    法人持股比例（5 档）

  企业画像（40% 权重 = 60 分满分）：
    - employee_count   企业参保人数（5 档）
    - biz_balance      对公账户日均余额（5 档）
    - biz_loan_count   企业现有贷款笔数（4 档）
    - biz_overdue_2y   企业近 2 年逾期（3 档，3+ 次一票否决）
    - biz_query_3m     近 3 月对公查询（3 档）

  合规风险（20% 权重 = 20 分满分，任一命中即一票否决）：
    - compliance_risk  合规风险自查（5 档，4 档异常均一票否决）

  行业景气（10% 权重 = 10 分满分，沿用 v4 industry）：
    - industry         所属行业（v4 已有）

选项 label 与前端 assess-options.ts v5 增量部分完全一致

用法：
  python -m scripts.init_business_v5_rules
"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models.scorecard import ScorecardRule
from app.utils.logger import logger


# ============================================================================
# 字段：(category, variable, option_label, score, type, is_veto, sort_order, product_type_id)
# ============================================================================

LEGAL_RULES: list[tuple] = [
    # ----- legal_form 组织形式（5 档）-----
    ("法人", "legal_form", "有限公司", 8, "business", 0, 400, None),
    ("法人", "legal_form", "股份有限公司", 8, "business", 0, 401, None),
    ("法人", "legal_form", "个人独资企业", 5, "business", 0, 402, None),
    ("法人", "legal_form", "合伙企业", 5, "business", 0, 403, None),
    ("法人", "legal_form", "个体工商户", 3, "business", 0, 404, None),
    # ----- legal_holding 法人持股比例（5 档）-----
    ("法人", "legal_holding", "100%", 10, "business", 0, 410, None),
    ("法人", "legal_holding", "51-99%", 7, "business", 0, 411, None),
    ("法人", "legal_holding", "30-50%", 4, "business", 0, 412, None),
    ("法人", "legal_holding", "<30%", 1, "business", 0, 413, None),
    ("法人", "legal_holding", "0%（代持）", 0, "business", 0, 414, None),
]


ENTERPRISE_RULES: list[tuple] = [
    # ----- employee_count 企业参保人数（5 档）-----
    ("企业", "employee_count", "100人以上", 12, "business", 0, 420, None),
    ("企业", "employee_count", "30-100人", 9, "business", 0, 421, None),
    ("企业", "employee_count", "10-30人", 6, "business", 0, 422, None),
    ("企业", "employee_count", "1-10人", 3, "business", 0, 423, None),
    ("企业", "employee_count", "0人", 0, "business", 0, 424, None),
    # ----- biz_balance 对公账户日均余额（5 档）-----
    ("企业", "biz_balance", "100万以上", 18, "business", 0, 430, None),
    ("企业", "biz_balance", "50-100万", 13, "business", 0, 431, None),
    ("企业", "biz_balance", "10-50万", 8, "business", 0, 432, None),
    ("企业", "biz_balance", "<10万", 3, "business", 0, 433, None),
    ("企业", "biz_balance", "几乎为零", 0, "business", 0, 434, None),
    # ----- biz_loan_count 企业现有贷款笔数（4 档）-----
    ("企业", "biz_loan_count", "0笔", 10, "business", 0, 440, None),
    ("企业", "biz_loan_count", "1-2笔", 7, "business", 0, 441, None),
    ("企业", "biz_loan_count", "3-5笔", 3, "business", 0, 442, None),
    ("企业", "biz_loan_count", "5笔以上", 0, "business", 0, 443, None),
    # ----- biz_overdue_2y 企业近 2 年逾期（3 档；3+ 次一票否决）-----
    ("企业", "biz_overdue_2y", "0次", 12, "business", 0, 450, None),
    ("企业", "biz_overdue_2y", "1-3次", 4, "business", 0, 451, None),
    ("企业", "biz_overdue_2y", "3次以上", 0, "business", 1, 452, None),  # ← 一票否决
    # ----- biz_query_3m 近 3 月对公查询（3 档）-----
    ("企业", "biz_query_3m", "0-2次", 8, "business", 0, 460, None),
    ("企业", "biz_query_3m", "3-5次", 4, "business", 0, 461, None),
    ("企业", "biz_query_3m", "6次以上", 0, "business", 0, 462, None),
]


# 合规风险：4 档"异常"全部一票否决（任一命中即拒批）
# 得分仅作显示用（实际被 veto 替换为 D/E）
COMPLIANCE_RULES: list[tuple] = [
    ("合规", "compliance_risk", "无任何异常", 20, "business", 0, 470, None),
    ("合规", "compliance_risk", "经营异常", 5, "business", 1, 471, None),  # ← 一票否决
    ("合规", "compliance_risk", "行政处罚", 5, "business", 1, 472, None),  # ← 一票否决
    ("合规", "compliance_risk", "司法风险", 5, "business", 1, 473, None),  # ← 一票否决
    ("合规", "compliance_risk", "失信被执行人", 0, "business", 1, 474, None),  # ← 一票否决
]


ALL_RULES = LEGAL_RULES + ENTERPRISE_RULES + COMPLIANCE_RULES


async def main():
    await init_db()
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            select(ScorecardRule.variable, ScorecardRule.option_label, ScorecardRule.product_type_id)
        )
        existing_set = set(
            (v, o, p if p is not None else None) for v, o, p in existing.all()
        )

        added = 0
        skipped = 0
        for cat, var, opt, score, type_, veto, order, ptid in ALL_RULES:
            key = (var, opt, ptid)
            if key in existing_set:
                skipped += 1
                continue
            rule = ScorecardRule(
                category=cat,
                variable=var,
                option_label=opt,
                score=float(score),
                type=type_,
                is_veto=veto,
                sort_order=order,
                product_type_id=ptid,
                enabled=1,
            )
            session.add(rule)
            added += 1
        await session.commit()
        logger.info(
            f"init_business_v5_rules: added={added}, skipped={skipped}, "
            f"legal={len(LEGAL_RULES)}, enterprise={len(ENTERPRISE_RULES)}, "
            f"compliance={len(COMPLIANCE_RULES)}"
        )
        print(
            f"✓ v5 business 规则已补全：新增 {added} 条，跳过 {skipped} 条已存在\n"
            f"  法人画像：{len(LEGAL_RULES)} 条（2 变量）\n"
            f"  企业画像：{len(ENTERPRISE_RULES)} 条（5 变量，含 1 条一票否决）\n"
            f"  合规风险：{len(COMPLIANCE_RULES)} 条（1 变量，含 4 条一票否决）\n"
            f"  行业景气：沿用 v4 industry"
        )


if __name__ == "__main__":
    asyncio.run(main())
