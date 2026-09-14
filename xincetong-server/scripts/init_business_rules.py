"""
补全 business 类型的评分卡规则（v4 P0+）

背景：
  init_scorecard.py 只初始化了 personal 4 大产品的规则，
  business 2 大产品（纳税贷 / 开票贷）的 7 个核心变量完全没规则，
  导致选 business 类型的用户走纳税贷/开票贷时 score=0（产品不可用）。

本次补全（v4）：
  7 个 business 变量通用规则（product_type_id=NULL，所有产品共用）
    - tax_grade        (纳税等级 A/M/B/C/D)
    - annual_tax       (年纳税额 区间)
    - tax_continuity   (纳税连续性 连续年数)
    - business_years   (企业经营年限)
    - annual_invoice   (年开票额 区间)
    - invoice_continuity (开票连续性)
    - industry         (行业 7 类)

  2 个产品的专属规则（product_type_id=5/6 加权）
    - 纳税贷：tax_grade + annual_tax + tax_continuity 权重 ×1.5
    - 开票贷：annual_invoice + invoice_continuity + industry 权重 ×1.5

选项 label 与前端 assess-options.ts (新增) 完全一致

用法：
  python -m scripts.init_business_rules
"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models.scorecard import ScorecardRule
from app.utils.logger import logger


# ============================================================================
# 通用规则（product_type_id=NULL，所有产品共用）
# 字段：(category, variable, option_label, score, type, is_veto, sort_order, product_type_id)
# ============================================================================

GENERAL_RULES: list[tuple] = [
    # ----- tax_grade 纳税等级（5 档）-----
    ("纳税", "tax_grade", "A 级",          18, "business", 0, 200, None),
    ("纳税", "tax_grade", "B 级",          12, "business", 0, 201, None),
    ("纳税", "tax_grade", "M 级",          10, "business", 0, 202, None),
    ("纳税", "tax_grade", "C 级",           4, "business", 0, 203, None),
    ("纳税", "tax_grade", "D 级/未评级",    0, "business", 0, 204, None),

    # ----- annual_tax 年纳税额（6 档）-----
    ("纳税", "annual_tax", "100万以上",    18, "business", 0, 210, None),
    ("纳税", "annual_tax", "50-100万",     14, "business", 0, 211, None),
    ("纳税", "annual_tax", "20-50万",      10, "business", 0, 212, None),
    ("纳税", "annual_tax", "5-20万",        6, "business", 0, 213, None),
    ("纳税", "annual_tax", "1-5万",         2, "business", 0, 214, None),
    ("纳税", "annual_tax", "1万以下",       0, "business", 0, 215, None),

    # ----- tax_continuity 纳税连续性（4 档）-----
    ("纳税", "tax_continuity", "连续3年",    10, "business", 0, 220, None),
    ("纳税", "tax_continuity", "连续2年",     6, "business", 0, 221, None),
    ("纳税", "tax_continuity", "连续1年",     3, "business", 0, 222, None),
    ("纳税", "tax_continuity", "断过/未缴",   0, "business", 0, 223, None),

    # ----- business_years 经营年限（4 档）-----
    ("经营", "business_years", "5年以上",     10, "business", 0, 230, None),
    ("经营", "business_years", "3-5年",        7, "business", 0, 231, None),
    ("经营", "business_years", "1-3年",        4, "business", 0, 232, None),
    ("经营", "business_years", "1年以下",      0, "business", 0, 233, None),

    # ----- annual_invoice 年开票额（5 档）-----
    ("经营", "annual_invoice", "1000万以上",  20, "business", 0, 240, None),
    ("经营", "annual_invoice", "500-1000万",  16, "business", 0, 241, None),
    ("经营", "annual_invoice", "200-500万",   12, "business", 0, 242, None),
    ("经营", "annual_invoice", "50-200万",     6, "business", 0, 243, None),
    ("经营", "annual_invoice", "50万以下",     0, "business", 0, 244, None),

    # ----- invoice_continuity 开票连续性（4 档）-----
    ("经营", "invoice_continuity", "连续3年",  10, "business", 0, 250, None),
    ("经营", "invoice_continuity", "连续2年",   6, "business", 0, 251, None),
    ("经营", "invoice_continuity", "连续1年",   3, "business", 0, 252, None),
    ("经营", "invoice_continuity", "断过/未开", 0, "business", 0, 253, None),

    # ----- industry 行业（7 类，限制类行业降分）-----
    ("经营", "industry", "制造业",            8, "business", 0, 260, None),
    ("经营", "industry", "批发零售",          6, "business", 0, 261, None),
    ("经营", "industry", "服务业",            6, "business", 0, 262, None),
    ("经营", "industry", "科技/互联网",      10, "business", 0, 263, None),
    ("经营", "industry", "建筑/工程",         4, "business", 0, 264, None),
    ("经营", "industry", "物流/运输",         4, "business", 0, 265, None),
    ("经营", "industry", "其他",              2, "business", 0, 266, None),
]


# ============================================================================
# 专属规则（product_type_id=5 纳税贷 / 6 开票贷，加权 ×1.5）
# ============================================================================

PRODUCT_RULES: list[tuple] = [
    # 纳税贷（id=5）: tax_grade + annual_tax + tax_continuity ×1.5
    ("纳税", "tax_grade",      "A 级",      27, "business", 0, 300, 5),
    ("纳税", "tax_grade",      "B 级",      18, "business", 0, 301, 5),
    ("纳税", "annual_tax",     "100万以上", 27, "business", 0, 310, 5),
    ("纳税", "annual_tax",     "50-100万",  21, "business", 0, 311, 5),
    ("纳税", "tax_continuity", "连续3年",   15, "business", 0, 320, 5),
    ("纳税", "tax_continuity", "连续2年",    9, "business", 0, 321, 5),
    ("纳税", "business_years", "5年以上",   15, "business", 0, 330, 5),
    ("纳税", "business_years", "3-5年",     10, "business", 0, 331, 5),

    # 开票贷（id=6）: annual_invoice + invoice_continuity + industry ×1.5
    ("经营", "annual_invoice",     "1000万以上", 30, "business", 0, 350, 6),
    ("经营", "annual_invoice",     "500-1000万", 24, "business", 0, 351, 6),
    ("经营", "annual_invoice",     "200-500万",  18, "business", 0, 352, 6),
    ("经营", "invoice_continuity", "连续3年",    15, "business", 0, 360, 6),
    ("经营", "invoice_continuity", "连续2年",     9, "business", 0, 361, 6),
    ("经营", "industry",           "科技/互联网", 15, "business", 0, 370, 6),
    ("经营", "industry",           "制造业",     12, "business", 0, 371, 6),
    ("经营", "business_years",     "3-5年",      10, "business", 0, 380, 6),
]


ALL_RULES = GENERAL_RULES + PRODUCT_RULES


async def main():
    await init_db()
    async with AsyncSessionLocal() as session:
        # 查已存在的 (variable, option_label, product_type_id) 三元组
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
            f"init_business_rules: added={added}, skipped={skipped}, "
            f"general={len(GENERAL_RULES)}, product={len(PRODUCT_RULES)}"
        )
        print(f"✓ 已补全 business 评分规则：新增 {added} 条，跳过 {skipped} 条已存在")


if __name__ == "__main__":
    asyncio.run(main())
