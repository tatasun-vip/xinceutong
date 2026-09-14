"""
信测通 · 报告一致性自审服务（v3.4）

核心职责：
  报告生成后，对最终输出做"自相矛盾"检查。
  如果发现矛盾，**自动修正**（不返回有矛盾的报告给用户）。
  同时把审计结果记录到 audit_log（让前端能感知）。

可避免的矛盾（自检覆盖）：
  1. D/E 级文案出现"基本符合/良好/直接申请"等乐观措辞
  2. S/A 级文案出现"暂缓/不建议/需先优化"等悲观措辞
  3. level 与 pass_probability 不一致（如 S 级 + 极低）
  4. E 级有非零额度
  5. level 与 收入倍数法 测算的额度 不匹配（D 级 200 万）
  6. 高额度 + 极低通过率（B/C 级额度 100 万+但通过率 极低）
  7. 0 个问题但 level 不是 S/A（无法解释为什么是 B/C）
  8. projection.target_level 不高于当前 level
  9. 利率与 level 不匹配
  10. 限速小数（limit_min > limit_max）

设计原则：
  - 修正优先于报错（用户体验优先）
  - 所有修正都通过 audit_log 记录
  - 前端 free 报告页可不显示 audit_log；管理后台可查
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("xincetong.auditor")


# ============================================================================
# 不变量定义
# ============================================================================

# level → 允许的通过率（银行实际模型）
LEVEL_VALID_PASS: dict[str, list[str]] = {
    "S": ["高", "中高"],
    "A": ["高", "中高", "中"],
    "B": ["中高", "中", "低"],
    "C": ["中", "低", "极低"],
    "D": ["低", "极低"],
    "E": ["极低"],
}

# level → 收入倍数合理范围（按银行实际产品授信区间校准）
# S: 优质客群 4-8 倍年收 + 公积金贷可到 200 倍月缴（折算上限约 12 倍年收）
# A: 4-8 倍
# B: 普通工薪 2-5 倍
# C: 弱客群 1-3 倍
# D: 极弱客群 0.3-1.5 倍
LEVEL_LIMIT_FACTOR: dict[str, tuple[float, float]] = {
    "S": (6.0, 12.0),
    "A": (4.0, 8.0),
    "B": (2.5, 5.0),
    "C": (1.0, 3.0),
    "D": (0.3, 1.5),
    "E": (0.0, 0.0),
}

# level → 利率合理范围
LEVEL_RATE_RANGE: dict[str, tuple[float, float]] = {
    "S": (3.5, 5.0),
    "A": (4.5, 7.0),
    "B": (6.0, 9.5),
    "C": (8.5, 14.0),
    "D": (12.0, 18.0),
    "E": (18.0, 24.0),
}


@dataclass
class AuditResult:
    """自审结果"""

    issues: list[str] = field(default_factory=list)  # 发现的矛盾
    fixes: list[str] = field(default_factory=list)   # 已自动修正
    warnings: list[str] = field(default_factory=list)  # 软警告

    @property
    def has_issue(self) -> bool:
        return bool(self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "issues": self.issues,
            "fixes": self.fixes,
            "warnings": self.warnings,
            "ok": not self.issues,
        }


# ============================================================================
# 主入口
# ============================================================================
def audit_and_fix_report(
    overall: dict[str, Any],
    one_sentence: str,
    top_issues: list[dict],
    projection: dict | None,
    annual_income: int = 0,
) -> tuple[dict[str, Any], str, list[dict], dict | None, AuditResult]:
    """
    对生成的报告做一致性自审，必要时自动修正。

    Args:
        overall:  {"score", "level", "limit_min", "limit_max", "rate_min", "rate_max", "pass_probability"}
        one_sentence: 当前生成的一句话结论
        top_issues: 核心问题列表
        projection: 改善后推演（可为 None）
        annual_income: 用户月收入×12（用于额度合理性校验）

    Returns:
        (修正后的 overall, 修正后的 one_sentence, 修正后的 top_issues, 修正后的 projection, AuditResult)
    """
    result = AuditResult()
    # 拷贝（避免修改入参）
    overall = dict(overall)
    top_issues = list(top_issues)
    projection = dict(projection) if projection else None

    level = overall.get("level", "E")
    score = overall.get("score", 0)
    pass_prob = overall.get("pass_probability", "极低")
    limit_min = overall.get("limit_min", 0)
    limit_max = overall.get("limit_max", 0)
    rate_min = overall.get("rate_min", 0)
    rate_max = overall.get("rate_max", 0)

    # ============ 1. 修正 pass_probability（level ↔ pass 一致性）============
    valid_passes = LEVEL_VALID_PASS.get(level, ["极低"])
    if pass_prob not in valid_passes:
        # 强制映射到该 level 允许的最接近的通过率
        # 按"最接近"原则（保留原语义但降级）
        if pass_prob == "高" and level == "D":
            new_pp = "低"
        elif pass_prob == "中高" and level in ("D",):
            new_pp = "低"
        elif pass_prob == "中" and level in ("D", "E"):
            new_pp = "极低"
        elif pass_prob == "低" and level == "E":
            new_pp = "极低"
        elif pass_prob in ("高", "中高") and level == "C":
            new_pp = "中"
        elif pass_prob in ("高", "中高", "中") and level in ("D", "E"):
            new_pp = "极低"
        else:
            new_pp = valid_passes[0]  # 取该 level 允许的第一档（最保守）
        result.fixes.append(
            f"pass_probability {pass_prob} 与 level {level} 不匹配，强制改为 {new_pp}"
        )
        overall["pass_probability"] = new_pp
        pass_prob = new_pp

    # ============ 2. 修正 E 级额度（必须为 0）============
    if level == "E":
        if limit_min != 0 or limit_max != 0:
            result.fixes.append(f"E 级额度 {limit_min}-{limit_max} 必须为 0，已清零")
            overall["limit_min"] = 0
            overall["limit_max"] = 0
            limit_min = limit_max = 0

    # ============ 3. 修正 limit_min > limit_max ============
    if limit_min > limit_max:
        result.fixes.append(
            f"limit_min {limit_min} > limit_max {limit_max}，交换"
        )
        overall["limit_min"] = limit_max
        overall["limit_max"] = limit_min
        limit_min, limit_max = limit_max, limit_min

    # ============ 4. 修正额度与 level 不匹配（基于收入倍数）============
    if annual_income > 0 and level != "E" and limit_max > 0:
        factor = limit_max / annual_income
        low, high = LEVEL_LIMIT_FACTOR[level]
        if factor > high:
            new_max = int(annual_income * high)
            new_min = int(new_max * 0.7)
            result.fixes.append(
                f"{level} 额度 {limit_max/10000:.0f}万 = {factor:.1f}倍年收入，"
                f"超出 {high:.1f}倍上限，改为 {new_max/10000:.0f}万"
            )
            overall["limit_min"] = new_min
            overall["limit_max"] = new_max
            limit_min, limit_max = new_min, new_max
        elif factor < low and level != "S":
            # 额度太低（罕見，但 defensive）
            new_max = int(annual_income * low)
            new_min = int(new_max * 0.7)
            result.fixes.append(
                f"{level} 额度 {limit_max/10000:.0f}万 = {factor:.1f}倍年收入，"
                f"低于 {low:.1f}倍下限，改为 {new_max/10000:.0f}万"
            )
            overall["limit_min"] = new_min
            overall["limit_max"] = new_max
            limit_min, limit_max = new_min, new_max

    # ============ 5. 修正高额度 + 极低通过率（防御性）============
    if limit_max >= 1000000 and pass_prob == "极低" and level in ("B", "C"):
        # 100万 + 极低 通过率 → 降额度到 100 万以下
        new_max = 800000
        new_min = int(new_max * 0.7)
        result.fixes.append(
            f"{level} 额度 {limit_max/10000:.0f}万 但通过率极低，已降至 {new_max/10000:.0f}万"
        )
        overall["limit_min"] = new_min
        overall["limit_max"] = new_max
        limit_min, limit_max = new_min, new_max

    # ============ 6. 修正利率范围 ============
    rate_low, rate_high = LEVEL_RATE_RANGE.get(level, (0, 100))
    if not (rate_low <= rate_min <= rate_high):
        new_min = max(rate_low, min(rate_min, rate_high))
        result.fixes.append(
            f"{level} 利率下限 {rate_min} 不在 ({rate_low}, {rate_high})，已修正为 {new_min}"
        )
        overall["rate_min"] = new_min
        rate_min = new_min
    if not (rate_low <= rate_max <= rate_high):
        new_max = max(rate_low, min(rate_max, rate_high))
        result.fixes.append(
            f"{level} 利率上限 {rate_max} 不在 ({rate_low}, {rate_high})，已修正为 {new_max}"
        )
        overall["rate_max"] = new_max
        rate_max = new_max
    if rate_min > rate_max:
        overall["rate_min"], overall["rate_max"] = rate_max, rate_min
        rate_min, rate_max = rate_max, rate_min

    # ============ 7. 修正 top_issues（确保与 level 一致）============
    n_total = len(top_issues)
    n_high = sum(1 for i in top_issues if i.get("severity") == "high")
    n_mid = sum(1 for i in top_issues if i.get("severity") == "mid")
    n_low = sum(1 for i in top_issues if i.get("severity") == "low")

    # E 级必须至少有 high/mid 问题
    if level == "E" and n_high == 0 and n_mid == 0:
        result.issues.append(f"E 级但无 high/mid 问题（{n_total} 个）")

    # 0 问题但 level 不是 S/A：模型异常，但不改（无法自动生成合理问题）
    if n_total == 0 and level not in ("S", "A"):
        result.warnings.append(
            f"{level} 级但无核心问题（{n_total}），按说应是 S/A 级（可能为评分模型异常）"
        )

    # S/A 级不该有 high
    if level in ("S", "A") and n_high > 0:
        result.warnings.append(f"{level} 级但有 {n_high} 个 high 问题（评分模型异常）")

    # ============ 8. 修正 projection（必须高于当前 level）============
    level_rank = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1, "E": 0}
    if projection:
        target = projection.get("level", "")
        if target and level_rank.get(target, -1) <= level_rank.get(level, -1):
            result.fixes.append(
                f"projection.target_level={target} 不高于当前 {level}，已清除"
            )
            projection = None

    # ============ 9. 修正 one_sentence（最终文案一致性）============
    fixed_text = _fix_one_sentence(
        text=one_sentence,
        level=level,
        n_high=n_high,
        n_mid=n_mid,
        n_low=n_low,
        n_total=n_total,
        pass_prob=pass_prob,
        has_projection=bool(projection),
    )
    if fixed_text != one_sentence:
        result.fixes.append(f"one_sentence 已修正：'{one_sentence}' → '{fixed_text}'")
        one_sentence = fixed_text

    return overall, one_sentence, top_issues, projection, result


def _fix_one_sentence(
    text: str,
    level: str,
    n_high: int,
    n_mid: int,
    n_low: int,
    n_total: int,
    pass_prob: str,
    has_projection: bool,
) -> str:
    """
    修正文案：必须包含 level 必含 token，不包含 forbidden token。
    若不满足，重写为该 level 的标准文案。
    """
    # level 必含 token
    required = {
        "S": ["优质", "申请"],
        "A": ["优质", "申请"],
        "B": ["良好"],
        "C": ["一般", "优化"],
        "D": ["较弱", "优化"],
        "E": ["暂缓", "优化"],
    }
    # level 必不含 token
    forbidden = {
        "S": ["暂缓", "不建议", "需先优化", "基本符合"],
        "A": ["暂缓", "不建议", "需先优化", "基本符合"],
        "B": ["暂缓", "不建议", "需先优化", "基本符合"],
        "C": ["优质", "极佳", "直接申请", "基本符合"],
        "D": ["优质", "极佳", "良好", "直接申请", "基本符合", "通过率较高"],
        "E": ["可直接申请", "良好", "通过率较高", "优质", "基本符合"],
    }

    # 检查是否一致
    needs_fix = False
    if not text:
        needs_fix = True
    for token in required.get(level, []):
        if token not in text:
            needs_fix = True
            break
    if not needs_fix:
        for token in forbidden.get(level, []):
            if token in text:
                needs_fix = True
                break
    # 0 问题但文案说"优化 N 个"
    if n_total == 0 and "优化" in text:
        import re
        m = re.search(r"优化\s*(\d+)\s*个", text)
        if m and int(m.group(1)) > 0:
            needs_fix = True

    if not needs_fix:
        return text

    # 重写为该 level 的标准文案
    if level in ("S", "A"):
        return f"您的资质已属{level}级优质，可直接申请"
    if level == "B":
        if pass_prob in ("高", "中高"):
            return "您的资质良好，可优先选择通过率较高的产品申请"
        return f"您的资质尚可，建议先优化 {n_total} 个细节再申请"
    if level == "C":
        if has_projection:
            return f"您的资质一般，先优化 {n_total} 个问题，预计通过率可提升"
        return f"您的资质一般，建议先优化 {n_total} 项指标再申请"
    if level == "D":
        if has_projection:
            return f"目前 {level} 级较弱，先优化 {n_total} 个问题，预计可提升至 C 级"
        return f"目前 {level} 级较弱，建议先优化 {n_total} 项关键指标再申请"
    # E
    return f"建议暂缓申请，先优化 {n_total} 个核心问题"
