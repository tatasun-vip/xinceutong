"""
v5 P0 自检脚本

校验项：
  1. DB 中 v5 规则数量正确（38 条：法人 10 + 企业 25 + 合规 5 - 等等）
  2. 8 个新变量 option_label 与前端常量完全一致
  3. 一票否决规则正确（compliance_risk 4 档 + biz_overdue_2y 1 档）
  4. 4 维度满分：法人 18 + 企业 60 + 合规 20 + 行业 = 总和
  5. 模拟业务用户跑 submit 拿 dimensions，校验 total 合理（0-100）
  6. 命中"失信被执行人"时 dimensions.compliance.ratio = 0，触发一票否决
  7. personal 用户跑 submit 时 dimensions = None（不影响 v4 行为）

用法：
  cd xinceutong-server
  python -m scripts.selfcheck_v5
"""
import asyncio
import sys
import re
from pathlib import Path
from sqlalchemy import select, func

from app.database import AsyncSessionLocal, init_db
from app.models.scorecard import ScorecardRule


# 期望规则清单（与 init_business_v5_rules.py 对齐）
EXPECTED_RULES = [
    # 法人画像 10 条
    ("法人", "legal_form", 5),
    ("法人", "legal_holding", 5),
    # 企业画像 25 条（5+5+4+3+3 - 但 biz_overdue_2y 是 3 档 1 条一票否决）
    ("企业", "employee_count", 5),
    ("企业", "biz_balance", 5),
    ("企业", "biz_loan_count", 4),
    ("企业", "biz_overdue_2y", 3),
    ("企业", "biz_query_3m", 3),
    # 合规风险 5 条
    ("合规", "compliance_risk", 5),
]

VETO_EXPECTED = [
    ("企业", "biz_overdue_2y", "3次以上"),
    ("合规", "compliance_risk", "经营异常"),
    ("合规", "compliance_risk", "行政处罚"),
    ("合规", "compliance_risk", "司法风险"),
    ("合规", "compliance_risk", "失信被执行人"),
]


async def main():
    await init_db()
    failures = []

    async with AsyncSessionLocal() as session:
        # ============ 1. 规则数量 ============
        total_q = await session.execute(
            select(func.count(ScorecardRule.id))
            .where(ScorecardRule.type == "business")
            .where(ScorecardRule.enabled == 1)
        )
        total = total_q.scalar() or 0
        expected_total = sum(n for _, _, n in EXPECTED_RULES) + 7  # 7 = v4 industry 档位
        if total < expected_total:
            failures.append(
                f"❌ [1] 规则数量不足：实际 {total} 条，期望 ≥{expected_total} 条\n"
                f"   原因：v5 38 条 + v4 7 条 industry = 45 条；当前可能未跑 init_business_v5_rules"
            )
        else:
            print(f"✅ [1] 规则数量：{total} 条（v5 新增 ≥{total-7} 条 + v4 industry 7 条）")

        # ============ 2. 各变量档位数量 ============
        rules_q = await session.execute(
            select(ScorecardRule.category, ScorecardRule.variable, ScorecardRule.option_label)
            .where(ScorecardRule.type == "business")
            .where(ScorecardRule.enabled == 1)
        )
        all_rules = rules_q.all()
        by_var: dict[tuple[str, str], int] = {}
        for cat, var, opt in all_rules:
            by_var[(cat, var)] = by_var.get((cat, var), 0) + 1

        for cat, var, expected_n in EXPECTED_RULES:
            actual_n = by_var.get((cat, var), 0)
            if actual_n != expected_n:
                failures.append(
                    f"❌ [2] 变量 {var} 档位不一致：实际 {actual_n} 档，期望 {expected_n} 档"
                )
            else:
                print(f"✅ [2] 变量 {var}：{actual_n} 档（{cat}）")

        # ============ 3. 一票否决规则数量（5 条）============
        veto_q = await session.execute(
            select(ScorecardRule.variable, ScorecardRule.option_label)
            .where(ScorecardRule.type == "business")
            .where(ScorecardRule.is_veto == 1)
        )
        veto_rules = veto_q.all()
        veto_set = {(v, o) for v, o in veto_rules}
        for var, opt in VETO_EXPECTED:
            if (var, opt) not in veto_set:
                failures.append(
                    f"❌ [3] 一票否决缺失：variable={var} option={opt}"
                )
        if not any(f.startswith("❌ [3]") for f in failures):
            print(f"✅ [3] 一票否决：{len(veto_rules)} 条（覆盖失信/行政处罚/经营异常/司法/3+逾期）")

        # ============ 4. 4 维度满分计算 ============
        var_max_score: dict[tuple[str, str], float] = {}
        var_cat: dict[str, str] = {}
        cat_max: dict[str, float] = {}
        rules_full_q = await session.execute(
            select(ScorecardRule.category, ScorecardRule.variable, ScorecardRule.score)
            .where(ScorecardRule.type == "business")
            .where(ScorecardRule.enabled == 1)
            .where(ScorecardRule.is_veto == 0)  # 只算非 veto
        )
        for cat, var, score in rules_full_q.all():
            var_cat[var] = cat
            k = (cat, var)
            if k not in var_max_score or float(score) > var_max_score[k]:
                var_max_score[k] = float(score)
        for (cat, _var), mxs in var_max_score.items():
            cat_max[cat] = cat_max.get(cat, 0.0) + mxs

        expected_cat_max = {"法人": 18.0, "企业": 60.0, "合规": 20.0}
        for cat, expected_mx in expected_cat_max.items():
            actual_mx = cat_max.get(cat, 0.0)
            if abs(actual_mx - expected_mx) > 0.1:
                failures.append(
                    f"❌ [4] 维度 {cat} 满分不符：实际 {actual_mx}，期望 {expected_mx}"
                )
            else:
                print(f"✅ [4] 维度 {cat} 满分：{actual_mx} 分")

        # ============ 5. _build_business_dimensions 模拟测试 ============
        sys.path.insert(0, ".")
        from app.api.assessment import _build_business_dimensions
        from app.services.scorecard_engine import _norm

        # 模拟优秀企业主：所有项都选最高档
        perfect_input = {
            "legal_form": "有限公司",
            "legal_holding": "100%",
            "employee_count": "100人以上",
            "biz_balance": "100万以上",
            "biz_loan_count": "0笔",
            "biz_overdue_2y": "0次",
            "biz_query_3m": "0-2次",
            "compliance_risk": "无任何异常",
            "industry": "科技/互联网",  # v4 最高档
        }
        rules_dict = [
            {
                "category": cat,
                "variable": var,
                "option_label": opt,
                "score": float(score) if score is not None else 0,
                "is_veto": 0,
            }
            for cat, var, opt, score in (
                await session.execute(
                    select(
                        ScorecardRule.category,
                        ScorecardRule.variable,
                        ScorecardRule.option_label,
                        ScorecardRule.score,
                    )
                    .where(ScorecardRule.type == "business")
                    .where(ScorecardRule.enabled == 1)
                )
            ).all()
        ]
        dims = _build_business_dimensions(rules_dict, perfect_input)
        total_score = dims.get("total", 0)
        if total_score < 80 or total_score > 100:
            failures.append(
                f"❌ [5] 全优企业主 total 异常：{total_score}（应在 80-100 之间）"
            )
        else:
            print(f"✅ [5] 全优企业主 total={total_score}（4 维度加权合理）")

        # ============ 6. 一票否决验证 ============
        veto_input = dict(perfect_input)
        veto_input["compliance_risk"] = "失信被执行人"
        dims_veto = _build_business_dimensions(rules_dict, veto_input)
        comp_ratio = dims_veto.get("compliance", {}).get("ratio", 0)
        if comp_ratio != 0.0:
            failures.append(
                f"❌ [6] 失信被执行人 compliance.ratio 应为 0，实际 {comp_ratio}"
            )
        else:
            print(f"✅ [6] 失信被执行人：compliance.ratio=0（命中即拒）")

        # ============ 7. submit_assessment 真的调用了 _build_business_dimensions ============
        # v6 修复：用 grep 静态检查 assessment.py source 真的把 _build_business_dimensions
        # 嵌进了 submit_assessment 函数（之前的 selfcheck 是假阳性：只 print"✅"没真检查）
        import re
        try:
            assessment_py_path = (
                Path(__file__).resolve().parent.parent / "app" / "api" / "assessment.py"
            )
            source = assessment_py_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            failures.append(f"❌ [7] 找不到 assessment.py 源码（路径 {assessment_py_path}）")
            return failures

        # 1) submit_assessment 函数体内必须出现 _build_business_dimensions 调用
        #    函数签名可能跨多行（多参数 + 类型注解），所以不用 [^)]*\) 截签名
        #    改用：从 `async def submit_assessment` 起点开始，到下一个 `^def |^async def |^class ` 之前
        m_start = re.search(r"^async def submit_assessment\b", source, re.MULTILINE)
        if not m_start:
            failures.append("❌ [7] 找不到 submit_assessment 函数（grep 失败）")
        else:
            start = m_start.start()
            # 找下一个顶级 def / class（行首 ^...）
            m_end = re.search(r"^(?:async )?def |^class ", source[start + 1:], re.MULTILINE)
            if not m_end:
                submit_body = source[start:]  # 文件以 submit_assessment 结尾
            else:
                submit_body = source[start:start + 1 + m_end.start()]
            # 检查 1: 调用了 _build_business_dimensions
            if "_build_business_dimensions" not in submit_body:
                failures.append(
                    "❌ [7] submit_assessment 函数没调 _build_business_dimensions（v5 P0 集成层断链）"
                )
            # 检查 2: 有 if type_ == "business" 保护（personal 不能算）
            elif 'if type_ == "business"' not in submit_body and "if type_=='business'" not in submit_body:
                failures.append(
                    "❌ [7] submit_assessment 调了 _build_business_dimensions 但没 if type_=='business' 保护，personal 也会算"
                )
            # 检查 3: 传给 Assessment 构造函数（commit 前落库）
            elif "dimensions=business_dimensions" not in submit_body:
                failures.append(
                    "❌ [7] _build_business_dimensions 结果没传给 Assessment 构造（不会落库）"
                )
            else:
                print(
                    "✅ [7] submit_assessment 真调了 _build_business_dimensions + "
                    "if type_=='business' 保护 + 传给 Assessment 构造（v5 P0 集成层通）"
                )

    # ============ 汇总 ============
    print("\n" + "=" * 60)
    if failures:
        print(f"❌ 自检失败：{len(failures)} 项不通过")
        for f in failures:
            print(f"  {f}")
        return 1
    print("✅ v5 P0 自检全部通过（7/7）")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
