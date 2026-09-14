#!/usr/bin/env python3
"""
信测通报告一致性自审 v2

按真实业务场景枚举所有可能的 (level, score, pass_prob, limit, issues, projection) 组合，
检查 (level, pass, limit, 严重度, 结论文案) 之间的不变量。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# 不变量定义（按银行实际审批逻辑）
# ============================================================================

# level → 允许的通过率（银行实际模型）
LEVEL_VALID_PASS = {
    "S": ["高", "中高"],
    "A": ["高", "中高", "中"],
    "B": ["中高", "中", "低"],
    "C": ["中", "低", "极低"],
    "D": ["低", "极低"],
    "E": ["极低"],
}

# level → 收入倍数合理范围（含 _calc_limits 的 0.7-1.3 波动）
LEVEL_LIMIT_FACTOR = {
    "S": (16.8, 31.2),    # 24×0.7 ~ 24×1.3
    "A": (12.6, 23.4),    # 18
    "B": (8.4, 15.6),     # 12
    "C": (5.6, 10.4),     # 8
    "D": (1.4, 2.6),      # 2
    "E": (0.0, 0.0),      # 0
}

# level → 结论文案的关键 token（必须出现）
LEVEL_REQUIRED_TOKEN = {
    "S": ["优质", "申请"],
    "A": ["优质", "申请"],
    "B": ["良好", "申请"],
    "C": ["一般", "优化"],     # 不能说"可直接申请"
    "D": ["较弱", "优化"],     # 不能说"可直接申请"
    "E": ["暂缓", "优化"],     # 拒批
}

# level → 结论文案必须 NOT 出现
LEVEL_FORBIDDEN_TOKEN = {
    "S": ["暂缓", "不建议", "不可", "需先优化"],
    "A": ["暂缓", "不建议", "不可", "需先优化"],
    "B": ["暂缓", "不建议", "不可"],
    "C": ["优质", "极佳", "直接申请"],  # C 级不能太乐观
    "D": ["优质", "极佳", "良好", "直接申请", "通过率较高"],
    "E": ["可直接申请", "良好", "通过率较高", "优质", "基本符合"],
}

# level → 利率合理范围
LEVEL_RATE_RANGE = {
    "S": (3.5, 5.0),
    "A": (4.5, 7.0),
    "B": (6.0, 9.5),
    "C": (8.5, 14.0),
    "D": (12.0, 18.0),
    "E": (18.0, 24.0),
}


# ============================================================================
# 自审函数
# ============================================================================
def audit_overall(level, score, pass_prob, limit_min, limit_max, rate_min, rate_max, annual_income):
    issues = []
    if pass_prob not in LEVEL_VALID_PASS.get(level, []):
        issues.append(f"[{level}/{score}分] 通过率 {pass_prob} 不在 {LEVEL_VALID_PASS[level]} 范围内")
    if annual_income > 0 and level != "E":
        factor = limit_max / annual_income
        low, high = LEVEL_LIMIT_FACTOR[level]
        if not (low <= factor <= high * 1.5):  # 综合分折扣后允许 0.3
            issues.append(f"[{level}/{score}分] 额度 {limit_max/10000:.0f}万 / 年收入 {annual_income/10000:.0f}万 = {factor:.1f}倍，应在 {low}-{high*1.5:.0f} 倍")
    if level == "E" and (limit_min > 0 or limit_max > 0):
        issues.append(f"[E] E 级必须额度=0，但 limit={limit_min}-{limit_max}")
    if limit_min > limit_max:
        issues.append(f"[{level}] limit_min {limit_min} > limit_max {limit_max}")
    if not (LEVEL_RATE_RANGE[level][0] <= rate_min <= LEVEL_RATE_RANGE[level][1]):
        issues.append(f"[{level}] 利率下限 {rate_min} 不在 {LEVEL_RATE_RANGE[level]}")
    if not (LEVEL_RATE_RANGE[level][0] <= rate_max <= LEVEL_RATE_RANGE[level][1]):
        issues.append(f"[{level}] 利率上限 {rate_max} 不在 {LEVEL_RATE_RANGE[level]}")
    if rate_min > rate_max:
        issues.append(f"[{level}] rate_min {rate_min} > rate_max {rate_max}")
    # 100万以上 + 极低通过率：不合理
    if limit_max >= 1000000 and pass_prob == "极低" and level not in ("D", "E"):
        issues.append(f"[{level}] 额度{limit_max/10000:.0f}万但通过率 极低（应是 100 万以下）")
    return issues


def audit_one_sentence(level, text, n_total, n_high, n_mid, n_low, pass_prob, has_projection):
    issues = []
    if not text:
        issues.append(f"[{level}] one_sentence 为空")
        return issues
    # 必含 token
    for token in LEVEL_REQUIRED_TOKEN.get(level, []):
        if token not in text:
            issues.append(f"[{level}] 文案缺关键词 '{token}'：{text}")
    # 必不出现 token
    for token in LEVEL_FORBIDDEN_TOKEN.get(level, []):
        if token in text:
            issues.append(f"[{level}] 文案禁用词 '{token}'：{text}")
    # 0 个问题不能要"优化 N 个"
    if n_total == 0 and "优化" in text and any(c.isdigit() and int(c) > 0 for c in text):
        # 提取"优化 N 个"看 N 是否 > 0
        import re
        m = re.search(r"优化\s*(\d+)\s*个", text)
        if m and int(m.group(1)) > 0:
            issues.append(f"[{level}] n_total=0 但文案说'优化 {m.group(1)} 个'：{text}")
    # projection 矛盾
    if has_projection and "预计可达" in text:
        import re
        m = re.search(r"可达\s*(\w+)\s*级", text)
        if m:
            target = m.group(1)
            rank = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1, "E": 0}
            if rank.get(target, -1) <= rank.get(level, -1):
                issues.append(f"[{level}] projection target {target} 不高于当前级别：{text}")
    return issues


def audit_top_issues(level, n_high, n_mid, n_low, has_projection, text):
    """top_issues 必须能解释为什么是当前 level"""
    issues = []
    n_total = n_high + n_mid + n_low
    # S/A 级不该有 high
    if level in ("S", "A") and n_high > 0:
        issues.append(f"[{level}/S-A] 不应有 high 问题，但 n_high={n_high}")
    # E 级必然有 high
    if level == "E" and n_high == 0 and n_mid == 0:
        issues.append(f"[E] E 级必须有 high 或 mid 问题，但全 0")
    # D/C 级应该有 mid 以上
    if level in ("C", "D") and n_high == 0 and n_mid == 0 and n_low == 0:
        issues.append(f"[{level}/C-D] 应有 mid+ 问题，但全 0（无法解释等级）")
    # 0 问题但 level 不是 S/A：异常
    if n_total == 0 and level not in ("S", "A"):
        issues.append(f"[{level}/0-problem] 0 问题但等级 {level}（正常应是 S/A）")
    return issues


# ============================================================================
# 跑测试
# ============================================================================
def run():
    print("=" * 90)
    print("信测通 · 报告一致性自审 v2")
    print("=" * 90)

    cases = [
        # (name, level, score, pass_prob, limit_min, limit_max, rate_min, rate_max, annual_income, n_high, n_mid, n_low, has_proj, one_sentence)

        # === 黄金客户 ===
        ("S级-高通过率", "S", 85, "高",  8000000, 12000000, 3.8, 4.5, 600000, 0, 0, 0, False, "您的资质已属优质，可直接申请"),
        ("A级-高通过率", "A", 75, "高",  5000000, 8000000,  5.0, 6.5, 500000, 0, 0, 0, False, "您的资质已属优质，可直接申请"),
        ("B级-中通过率", "B", 60, "中",  2000000, 4000000,  7.0, 9.0, 400000, 0, 0, 1, False, "您的资质良好，可优先选择通过率较高的产品申请"),

        # === D 级用户（用户截图情况）===
        ("D级-低通过率", "D", 35, "低",  400000, 800000,  14.0, 16.0, 400000, 0, 1, 1, True, "目前 D 级较弱，先优化 2 个问题，预计可达 B 级"),
        ("D级-极低通过率", "D", 30, "极低", 200000, 400000, 15.0, 18.0, 400000, 1, 0, 0, False, "建议暂缓申请，先优化 1 个核心问题"),

        # === C 级（最容易矛盾的）===
        ("C级-低通过率", "C", 42, "低",  1000000, 2000000, 10.0, 13.0, 300000, 0, 1, 0, True, "您的资质一般，建议先优化 1 项指标再申请"),
        ("C级-有projection", "C", 42, "中", 1500000, 2500000, 9.0, 12.0, 300000, 0, 0, 1, True, "资质一般，先优化 1 个问题，预计可达 B 级"),

        # === 0 问题（容易矛盾）===
        ("B级-0问题",   "B", 60, "中高", 2000000, 4000000, 7.0, 9.0, 400000, 0, 0, 0, False, "您的资质良好，可优先选择通过率较高的产品申请"),
        ("C级-0问题",   "C", 45, "中",  1000000, 2000000, 10.0, 13.0, 300000, 0, 0, 0, False, "您的资质一般，建议先优化 0 项指标再申请"),

        # === 反面案例（应被自审捕获）===
        ("反面-基本符合", "D", 35, "极低", 200000, 400000, 14.0, 18.0, 400000, 0, 1, 0, False, "您的资质基本符合申请条件，建议优先选择通过率较高的产品"),
        ("反面-高额极低", "B", 60, "极低", 3000000, 5000000, 8.0, 10.0, 400000, 0, 0, 1, False, "您的资质良好，可直接申请"),
        ("反面-E级有额", "E", 10, "极低", 100000, 200000, 18.0, 22.0, 0, 1, 0, 0, False, "建议暂缓申请，先优化 1 个核心问题"),
        ("反面-0问E级", "E", 10, "极低", 0, 0, 18.0, 22.0, 0, 0, 0, 0, False, "建议暂缓申请，先优化 0 个核心问题"),
        ("反面-S级high", "S", 85, "高", 8000000, 12000000, 3.8, 4.5, 600000, 1, 0, 0, False, "您的资质已属优质，可直接申请"),
        ("反面-C级良好", "C", 45, "中", 1000000, 2000000, 10.0, 13.0, 300000, 0, 1, 0, False, "您的资质良好，可直接申请"),
        ("反面-D级直申", "D", 35, "低",  400000, 800000,  14.0, 16.0, 400000, 0, 0, 1, False, "您的资质良好，可直接申请"),

        # === 改善后变差的 projection ===
        ("反面-proj差", "B", 60, "中高", 2000000, 4000000, 7.0, 9.0, 400000, 0, 0, 0, True, "您的资质良好，先优化 0 个问题，预计可达 B 级"),

        # === 利率矛盾 ===
        ("反面-利率高", "S", 85, "高", 8000000, 12000000, 3.8, 4.5, 600000, 0, 0, 0, False, "您的资质已属优质，可直接申请"),
        ("正面-利率", "A", 75, "中高", 5000000, 8000000, 4.5, 7.0, 500000, 0, 0, 0, False, "您的资质已属优质，可直接申请"),
    ]

    total_issues = 0
    for i, c in enumerate(cases, 1):
        name = c[0]
        level, score, pp, lm, lM, rm, rM, inc, nh, nm, nl, hp, text = c[1:]
        all_issues = []
        all_issues += audit_overall(level, score, pp, lm, lM, rm, rM, inc)
        all_issues += audit_one_sentence(level, text, nh + nm + nl, nh, nm, nl, pp, hp)
        all_issues += audit_top_issues(level, nh, nm, nl, hp, text)
        if all_issues:
            print(f"\n[{i:2}] {name} ❌ {len(all_issues)} 处")
            for iss in all_issues:
                print(f"      → {iss}")
            total_issues += len(all_issues)
        else:
            print(f"[{i:2}] {name} ✅")

    print("\n" + "=" * 90)
    print(f"审计结果：发现 {total_issues} 处矛盾")
    print("=" * 90)
    return total_issues


if __name__ == "__main__":
    sys.exit(0 if run() == 0 else 1)
