"""
6 大产品独立评分引擎（v3 核心）

按用户最新文案：
  - 一次输入，6 套独立模型跑出 6 个产品结果
  - 每套模型：通用规则 + 该产品专属规则
  - 每套模型：按 product_types.limit_formula 选独立额度公式
  - 每套模型：按 product_types.rate_min/rate_max 配置利率区间

输入：input_data + user_type
输出：list[ProductResult]，6 个产品（启用 + 匹配 user_type）

设计原则：
  - 评分卡规则（_load_rules）按 product_type_id 加载（NULL=通用 + X=专属）
  - 额度公式（_calc_limit_for_product）按 product_types.limit_formula 选函数
  - 通过概率（_calc_pd_and_pass）按 score 等级映射（与原引擎一致）
  - 风险标签 / 优势（_build_tags）按 product_type.focus_vars 重点变量生成
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_type import ProductType
from app.models.scorecard import ScorecardRule
from app.services.scorecard_engine import (
    LEVEL_THRESHOLDS,
    PASS_PROB_MAP,
    RATE_MIN_BY_LEVEL,
    RATE_MAX_BY_LEVEL,
    _build_tags,
    _check_veto,
    _level_of,
    _normalize,
    _score_items,
)
from app.utils.logger import logger
from app.utils.money import (
    car_value,
    housing_fund_value,
    house_value,
    income_value,
    min_of,
    monthly_debt_value,
)
from app.services.bank_scorecard import (
    apply_bank_bias as _apply_bank_bias,
    get_bank_limit_boost as _get_bank_limit_boost,
    is_veto_relax as _is_veto_relax,
)


# ============================================================================
# 渠道合规硬上限（按产品+渠道）
# ============================================================================
# 监管依据：
#   1. 银保监会 2020 年 7 月《关于加强商业银行互联网贷款业务管理》
#      —— 单户用于消费的个人授信 ≤ 30 万元（线上互联网贷款）
#   2. 商业银行自营消费贷（线下）行业惯例 ≤ 100 万元
#   3. 公积金中心：单职工 60 万 / 双职工 120 万（按城市不同有差异）
#   4. 个人经营性贷款（线下） ≤ 500-1000 万（需担保/抵押）
#   5. 小微企业税银贷（线上）：微众/网商 500 万上限
#   6. 房抵贷（二抵）≤ 1000 万（需评估净值）
#
# 设计原则（按用户要求）：
#   - 信用贷款（无抵押/无担保）有上限，不能因为用户填的数值好就任意放大
#   - 线上额度低（监管严 + 风险控制严）→ 30 万
#   - 线下额度高（面签 + 收入证明 + 强担保）→ 100 万
#   - 测算值 > 上限 → 取上限（不能让"用户好数据"测算出银行实际给不到的额度）
CHANNEL_CAPS: dict[str, dict[str, int]] = {
    # 优质单位贷：建行快贷/工行融e借/招行闪电贷（线上 30、线下 100）
    "quality_unit": {"online": 30_0000, "offline": 100_0000},
    # 公积金贷：招行/建行公积金优享贷（线上 30、线下 120，双职工最高 120）
    "housing_fund": {"online": 30_0000, "offline": 120_0000},
    # 工薪贷：平安新一贷/民生民易贷（线上 30、线下 100）
    "salary": {"online": 30_0000, "offline": 100_0000},
    # 有房客户贷（房抵贷/二抵，线下为主）：≤ 1000 万（含抵押）
    "house_owner": {"online": 50_0000, "offline": 1000_0000},
    # 纳税贷（个人）：建行税易贷（线上 30、线下 100；企业版可到 500）
    "tax": {"online": 30_0000, "offline": 100_0000},
    # 开票贷（小微企业）：网商/微众开票贷（线上 100、线下 500）
    "invoice": {"online": 100_0000, "offline": 500_0000},
}


# ============================================================================
# 实际可贷金额折扣（按综合等级）
# ============================================================================
# 银行实操：S/A 维持测算值；B 级打 5 折（中等客群实际授信 50%）；C 打 3 折；
# D 打 1.5 折（弱客群银行实际给得更少）；E 拒批（0）。
#
# 设计原则：避免"测算额度虚高"问题（用户看到 50 万，实际去银行只给 10 万）
# 与 synthesize_overall_score 共用此常量。
_LIMIT_DISCOUNT: dict[str, float] = {
    "S": 1.0, "A": 1.0, "B": 0.5, "C": 0.3, "D": 0.15, "E": 0.0,
}


# ============================================================================
# 6 产品证据链构建（A2 深度证据链设计）
# ============================================================================


def _build_evidence(
    items: list[dict],
    rules: list[dict],
    score: int,
    level: str,
    limit_min_capped: int,
    limit_max_capped: int,
) -> dict:
    """6 产品独立证据链构建

    从 items（用户实际命中的规则）提取 4 类信息 + 1 个实际可贷金额：

    Returns:
        {
          "hit_rules": [{"rule", "score", "category"}, ...],   # 命中高分 top 3
          "low_rules": [{"rule", "score", "category"}, ...],   # 命中低分 top 3
          "improve_vars": [{"var", "current", "best", "delta"}, ...],  # 提分变量 top 3
          "not_recommend_reason": "str",                          # 不推荐原因（1-2 句）
          "realistic_limit_min": int,                            # 实际可贷下限
          "realistic_limit_max": int,                            # 实际可贷上限
        }
    """
    # 1. 命中规则（高分）：score > 0，按 score desc 取 top 3
    positive = [it for it in items if it["score"] > 0]
    positive.sort(key=lambda x: x["score"], reverse=True)
    hit_rules = [
        {
            "rule": it["option_label"],
            "score": round(it["score"], 1),
            "category": it.get("category") or "",
        }
        for it in positive[:3]
    ]

    # 2. 命中规则（低分）：score < 0，按 score asc 取 top 3
    negative = [it for it in items if it["score"] < 0]
    negative.sort(key=lambda x: x["score"])
    low_rules = [
        {
            "rule": it["option_label"],
            "score": round(it["score"], 1),
            "category": it.get("category") or "",
        }
        for it in negative[:3]
    ]

    # 3. 提分变量：每个 low_rule 找同 variable 的最高分 option → 计算 delta
    #    （"如果用户改为最佳选项，可以+多少分"）
    improve_vars: list[dict] = []
    for lr in negative:
        var = lr["variable"]
        same_var_rules = [r for r in rules if r["variable"] == var and not r.get("is_veto")]
        if not same_var_rules:
            continue
        best = max(same_var_rules, key=lambda r: r["score"])
        if best["score"] > lr["score"] and best["option_label"] != lr["option_label"]:
            improve_vars.append({
                "var": var,
                "current": lr["option_label"],
                "best": best["option_label"],
                "delta": round(best["score"] - lr["score"], 1),
            })
    improve_vars.sort(key=lambda x: x["delta"], reverse=True)
    improve_vars = improve_vars[:3]

    # 4. 不推荐原因：基于 low_rules + level 聚合，1-2 句中文
    not_recommend_reason = ""
    if level == "E":
        if low_rules:
            rules_text = "；".join(lr["rule"] for lr in low_rules[:2])
            not_recommend_reason = f"扣分项：{rules_text}，建议先解决风险项"
        else:
            not_recommend_reason = "当前资质不符合准入条件，建议先解决风险项"
    elif level == "D":
        if low_rules:
            rules_text = "；".join(lr["rule"] for lr in low_rules[:2])
            not_recommend_reason = f"综合分偏低（{score} 分），主要扣分项：{rules_text}"
        else:
            not_recommend_reason = f"综合分偏低（{score} 分），建议 3-6 个月改善后申请"
    elif level == "C" and low_rules:
        rules_text = "；".join(lr["rule"] for lr in low_rules[:2])
        not_recommend_reason = f"可优化项：{rules_text}"

    # 5. 实际可贷金额：limit × _LIMIT_DISCOUNT（按本产品等级）
    discount = _LIMIT_DISCOUNT.get(level, 0.5)
    if limit_min_capped > 0:
        realistic_min = _round_to_nice(int(limit_min_capped * discount))
        realistic_max = _round_to_nice(int(limit_max_capped * discount))
    else:
        realistic_min = 0
        realistic_max = 0

    return {
        "hit_rules": hit_rules,
        "low_rules": low_rules,
        "improve_vars": improve_vars,
        "not_recommend_reason": not_recommend_reason,
        "realistic_limit_min": realistic_min,
        "realistic_limit_max": realistic_max,
    }


# ============================================================================
# 渠道合规 Cap 工具
# ============================================================================


def _round_to_nice(v: int | float, step: int = 5000) -> int:
    """v7 增量：把额度取整到 step 的整数倍（约数），让展示更"圆"
    
    业务诉求：模拟测算的额度（如 51638 元）太碎，给用户看像瞎编的。
    改成 round 到 5000 的整数倍后（55000 / 70000），更接近银行实际放款区间。
    
    边界：
      - 0 直接返回 0（避免给已否决的额度乱圆整）
      - < step 直接 round 到 step
    """
    v = int(v)
    if v <= 0:
        return 0
    return max(step, int(round(v / step)) * step)


def apply_channel_cap(
    product_code: str,
    limit_min: int,
    limit_max: int,
) -> tuple[int, int, bool, str]:
    """
    把测算额度按 CHANNEL_CAPS 限高。

    返回：(limit_min_capped, limit_max_capped, was_capped, reason)

    设计：
      - 当 limit_max 超过线下上限时，说明「按用户数据测算已经远超银行能给的最高额度」，
        此时将 limit_min / limit_max 同步 cap 到合理区间，并返回提示文案
      - 当 limit_max 未超过任何上限时，原样返回

    经验区间（按用户实际数据填得"好"时大概率触发）：
      - 月入 4 万，8x 优质单位贷 → 38 万  ← 不 cap
      - 月入 10 万，8x → 96 万  ← 不 cap（线下 100 万内）
      - 月入 20 万，8x → 192 万  ← cap 到 100 万
      - 月缴 3500，200x 公积金 → 84 万  ← 不 cap（线下 120 万内）
      - 月缴 8000，200x → 192 万  ← cap 到 120 万
    """
    caps = CHANNEL_CAPS.get(product_code)
    if not caps:
        return limit_min, limit_max, False, ""
    online_cap = caps["online"]
    offline_cap = caps["offline"]
    was_capped = False
    reason_parts = []
    # 当上限区间本身就超过线下硬上限 → 整体 cap
    if limit_max > offline_cap:
        # 按比例缩放 limit_min（保持 0.85-1.15 区间）
        scale = offline_cap / limit_max if limit_max > 0 else 1.0
        limit_min_capped = int(limit_min * scale)
        limit_max_capped = int(limit_max * scale)
        was_capped = True
        reason_parts.append(
            f"测算值 {limit_max/10000:.0f} 万超过「线下最高 {offline_cap/10000:.0f} 万」监管上限，已按线下额度 cap"
        )
    else:
        limit_min_capped = limit_min
        limit_max_capped = limit_max
    # v7 增量：圆整到 5000 整数倍，让展示更"圆"（如 51638 → 55000）
    limit_min_capped = _round_to_nice(limit_min_capped)
    limit_max_capped = _round_to_nice(limit_max_capped)
    return limit_min_capped, limit_max_capped, was_capped, "; ".join(reason_parts)


# ============================================================================
# 数据类
# ============================================================================


@dataclass
class ProductResult:
    """单个产品的测算结果"""

    product_code: str
    product_name: str
    product_subtitle: str
    score: int
    level: str
    raw_score: float
    limit_min: int = 0          # 元
    limit_max: int = 0          # 元
    rate_min: float = 0.0
    rate_max: float = 0.0
    pd: float = 0.0
    pass_probability: str = "极低"
    formula_used: str = ""
    focus_vars: list[str] = field(default_factory=list)
    key_points: list[str] = field(default_factory=list)
    matched_items: list[dict[str, Any]] = field(default_factory=list)
    risk_tags: list[str] = field(default_factory=list)
    advantages: list[str] = field(default_factory=list)
    weak_points: list[str] = field(default_factory=list)
    # 产品维度的"是否推荐展示"标志（DB 静态配置，用于产品介绍页）
    recommend: int = 0
    # 用户维度的"当前最适合该用户"标志（动态计算：score 最高且非 E/极低）
    # 报告页只显示这个，避免出现"⭐ + 通过率极低"的矛盾
    best_for_user: bool = False
    # 详细说明（满分 100 / 总分 / 通过概率等）
    description: str = ""
    veto: dict[str, Any] | None = None
    # P2 渠道合规字段
    channel_online_max: int = 0   # 线上渠道上限（元）
    channel_offline_max: int = 0  # 线下渠道上限（元）
    limit_capped: bool = False     # 测算值是否被渠道 cap 了
    limit_reason: str = ""         # 被 cap 的原因（生成给用户看）
    # v9 增量：6 产品独立证据链（A2 深度证据链设计）
    hit_rules: list[dict] = field(default_factory=list)
    """命中的高分规则 top3（按 score desc），用于「命中规则」展示：
       [{"rule": "公积金连续缴存 3 年以上", "score": +8, "category": "收入"}, ...]"""
    low_rules: list[dict] = field(default_factory=list)
    """命中的低分/扣分规则 top3（按 score asc），用于「不推荐原因」展示：
       [{"rule": "信用卡使用率 80%以上", "score": -5, "category": "征信"}, ...]"""
    not_recommend_reason: str = ""
    """不推荐原因（基于 low_rules 聚合 + level 推断），1-2 句中文给用户看：
       「近 3 个月查询 6 次以上（-6 分），建议 90 天后再申请」"""
    improve_vars: list[dict] = field(default_factory=list)
    """提分变量（命中负分项 → 若改为最佳选项可获得的提分），用于「提分变量」展示：
       [{"var": "credit_card_usage", "current": "80%以上", "best": "30%以下", "delta": +5}, ...]"""
    realistic_limit_min: int = 0  # 实际可贷下限（综合等级折扣后 + 渠道 cap 后）
    realistic_limit_max: int = 0  # 实际可贷上限
    """实际可贷金额 = 测算金额 × 综合等级折扣 × 渠道 cap
       与 limit_min/limit_max 区别：limit_min/max 是公式直算值，realistic 是用户实际能拿到的"""

    def to_dict(self) -> dict:
        return {
            "product_code": self.product_code,
            "product_name": self.product_name,
            "product_subtitle": self.product_subtitle,
            "score": self.score,
            "level": self.level,
            "raw_score": round(self.raw_score, 2),
            "limit_min": self.limit_min,
            "limit_max": self.limit_max,
            "rate_min": self.rate_min,
            "rate_max": self.rate_max,
            "pd": round(self.pd, 4),
            "pass_probability": self.pass_probability,
            "formula_used": self.formula_used,
            "focus_vars": self.focus_vars,
            "key_points": self.key_points,
            "matched_items": self.matched_items,
            "risk_tags": self.risk_tags,
            "advantages": self.advantages,
            "weak_points": self.weak_points,
            "recommend": self.recommend,
            "best_for_user": self.best_for_user,
            "description": self.description,
            "veto": self.veto,
            # P2 渠道合规字段
            "channel_online_max": self.channel_online_max,
            "channel_offline_max": self.channel_offline_max,
            "limit_capped": self.limit_capped,
            "limit_reason": self.limit_reason,
            # v9 增量：6 产品独立证据链
            "hit_rules": self.hit_rules,
            "low_rules": self.low_rules,
            "not_recommend_reason": self.not_recommend_reason,
            "improve_vars": self.improve_vars,
            "realistic_limit_min": self.realistic_limit_min,
            "realistic_limit_max": self.realistic_limit_max,
        }


# ============================================================================
# 规则加载（按产品维度）
# ============================================================================


async def _load_rules_for_product(
    type_: str, db: AsyncSession, product_type_id: int
) -> list[dict]:
    """
    加载某个产品的规则：
    - product_type_id = NULL（通用规则，所有产品都适用）
    - product_type_id = X（X 产品的专属规则）

    专属规则覆盖通用规则（同 variable + option_label 时优先专属）
    """
    from sqlalchemy import or_

    stmt = select(ScorecardRule).where(
        ScorecardRule.enabled == 1,
        or_(
            ScorecardRule.product_type_id.is_(None),
            ScorecardRule.product_type_id == product_type_id,
        ),
    )
    res = await db.execute(stmt)
    rows = res.scalars().all()

    # 通用规则
    common = [r for r in rows if r.product_type_id is None and r.type in (type_, "both")]
    # 专属规则
    specific = [r for r in rows if r.product_type_id == product_type_id]

    # 合并：先用通用 + 专属（去重，var+option 同 key 专属覆盖通用）
    merged: dict[tuple[str, str], Any] = {}
    for r in common:
        merged[(r.variable, r.option_label)] = r
    for r in specific:
        merged[(r.variable, r.option_label)] = r  # 覆盖

    return [
        {
            "variable": r.variable,
            "option_label": r.option_label,
            "category": r.category,
            "score": float(r.score),
            "type": r.type,
            "is_veto": r.is_veto,
            "product_type_id": r.product_type_id,
        }
        for r in merged.values()
    ]


# ============================================================================
# 6 大产品独立额度公式
# ============================================================================


def _calc_limit_quality_unit(data: dict, level: str) -> tuple[int, int, float, float]:
    """优质单位贷：年收入 × 4-8 倍（按等级），利率 3.6-5.5%

    银行实操：公务员/事业单位/世界 500 强客群，建行快贷/工行融e借/招行闪电贷
    给到 4-8 倍年收入。S 级 8 倍已是乐观上限（A 级 6 倍、B 级 4 倍更稳）。
    """
    income = income_value(data.get("monthly_income", ""))
    if level == "E" or income == 0:
        return 0, 0, 0, 0
    multiplier = {"S": 8, "A": 6, "B": 4, "C": 2.5, "D": 1.5}.get(level, 4)
    limit_min = int(income * 12 * multiplier * 0.85)
    limit_max = int(income * 12 * multiplier * 1.15)
    return limit_min, limit_max, 3.6, 5.5


def _calc_limit_housing_fund(data: dict, level: str) -> tuple[int, int, float, float]:
    """公积金贷：月缴存 × 12 × 100-200 倍（按等级），利率 3.45-5.5%

    银行实操：建行/工行/招行公积金优享贷，按月缴存 100-200 倍测算。
    月缴 2000 × 200 × 12 = 480 万（理论上限），S 级已偏乐观。
    """
    fund = housing_fund_value(data.get("housing_fund", ""))
    if level == "E" or fund == 0:
        return 0, 0, 0, 0
    multiplier = {"S": 200, "A": 150, "B": 100, "C": 60, "D": 24}.get(level, 100)
    limit_min = int(fund * 12 * multiplier * 0.85)
    limit_max = int(fund * 12 * multiplier * 1.15)
    return limit_min, limit_max, 3.45, 5.5


def _calc_limit_salary(data: dict, level: str) -> tuple[int, int, float, float]:
    """工薪贷：年收入 × 2-5 倍（按等级），利率 6-9%

    银行实操：平安新一贷/民生民易贷/中行随心智贷，
    普通工薪客群 2-3 倍年收入，优质工薪（如代发）可到 4-5 倍。
    """
    income = income_value(data.get("monthly_income", ""))
    if level == "E" or income == 0:
        return 0, 0, 0, 0
    multiplier = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1.2}.get(level, 3)
    limit_min = int(income * 12 * multiplier * 0.85)
    limit_max = int(income * 12 * multiplier * 1.15)
    return limit_min, limit_max, 6.0, 9.0


def _calc_limit_house_owner(data: dict, level: str) -> tuple[int, int, float, float]:
    """有房客户贷：房产净值 × 成数 - DSR，利率 4.8-7.5%

    银行实操：房产二次抵押（净值=评估-已有按揭），最高 50-70% 抵押率；
    弱客群 D=30% 抵押率（银行实际对负债高的房产主更严格）。
    """
    house = house_value(data.get("house", ""))
    car = car_value(data.get("car", ""))
    income = income_value(data.get("monthly_income", ""))
    monthly_debt = monthly_debt_value(data.get("monthly_debt", "") or "无")
    if level == "E" or house == 0:
        return 0, 0, 0, 0
    # 净值：按等级估算按揭比例（弱客群按揭比例往往更高）
    _NET_RATIO = {"S": 0.85, "A": 0.75, "B": 0.65, "C": 0.55, "D": 0.4}
    net_ratio = _NET_RATIO.get(level, 0.5)
    house_net = house if data.get("house") == "无按揭" else house * net_ratio
    asset_value = house_net + car
    # 抵押成数（已比旧的 0.7/0.6/0.5/0.4/0.3 下调 5-10pp）
    mortgage_rate = {"S": 0.65, "A": 0.55, "B": 0.45, "C": 0.35, "D": 0.2}.get(level, 0.4)
    # DSR 约束：最大月还款 = (月收入 - 月负债) × 0.5
    available_monthly = max(0, (income - monthly_debt)) * 0.5
    rate_pct = 0.06  # 中位 6.0%
    monthly_rate = rate_pct / 12
    n = 36
    if available_monthly > 0 and monthly_rate > 0:
        limit_dsr = available_monthly * (1 - (1 + monthly_rate) ** (-n)) / monthly_rate
    else:
        limit_dsr = 0
    # 资产法额度
    limit_asset = asset_value * mortgage_rate
    # 取最小
    chosen = min_of([limit_asset, limit_dsr])
    if chosen == 0:
        return 0, 0, 0, 0
    limit_min = int(chosen * 0.85)
    limit_max = int(chosen * 1.15)
    return limit_min, limit_max, 4.8, 7.5


def _calc_limit_tax(data: dict, level: str) -> tuple[int, int, float, float]:
    """纳税贷：年纳税额 × 5-10 倍（按等级），利率 5-9%

    银行实操：建行/工行税易贷/微众银行微业贷，按近 1-2 年纳税额 5-10 倍授信。
    S 级 10 倍已偏乐观，正常 B 级客户给到 4-5 倍。

    v9 修复：个人流程表单无 annual_tax 字段时，按 income + tax label 兜底估算：
      - tax label: 高=15%个税率, 中=10%, 低=5%, 无=0%
      - annual_tax ≈ 月收入 × 12 × 个税率（按当地累进近似）
      - 数据全缺则继续返回 0（让该产品 E 等级自然被淘汰）
    """
    # 1) 尝试读 annual_tax 字段（如有）
    annual_tax_str = data.get("annual_tax", "")
    annual_tax = 0
    if annual_tax_str:
        try:
            annual_tax = int(annual_tax_str)
        except ValueError:
            annual_tax_map = {
                "1万以下": 5000,
                "1-5万": 30000,
                "5-20万": 125000,
                "20-50万": 350000,
                "50-100万": 750000,
                "100万以上": 1500000,
            }
            annual_tax = annual_tax_map.get(annual_tax_str, 0)

    # 2) 兜底：按 income + tax label 估算（个人流程用）
    if annual_tax == 0:
        tax_label = data.get("tax", "")
        tax_rate_map = {"高": 0.15, "中": 0.10, "低": 0.05}
        rate = tax_rate_map.get(tax_label, 0)
        if rate > 0:
            income = income_value(data.get("monthly_income", ""))
            if income > 0:
                annual_tax = int(income * 12 * rate)

    if level == "E" or annual_tax == 0:
        return 0, 0, 0, 0
    multiplier = {"S": 10, "A": 8, "B": 5, "C": 3, "D": 1.5}.get(level, 5)
    limit_min = int(annual_tax * multiplier * 0.85)
    limit_max = int(annual_tax * multiplier * 1.15)
    return limit_min, limit_max, 5.0, 9.0


def _calc_limit_invoice(data: dict, level: str) -> tuple[int, int, float, float]:
    """开票贷：年开票额 × 5-10%，利率 6-12%

    银行实操：网商银行/微众银行/京东金融开票贷，按近 1 年开票额 5-10% 授信。
    S 级 10% 是优质企业上限，B 级 5-6% 是普通小微企业常见值。

    v9 修复：个人流程表单无 annual_invoice 字段时，按 income + invoice label 兜底：
      - invoice label: 高=月收入×5倍, 中=3倍, 低=1.5倍（模拟小规模经营者的开票量）
      - 数据全缺则继续返回 0
    """
    annual_invoice_str = data.get("annual_invoice", "")
    annual_invoice = 0
    if annual_invoice_str:
        try:
            annual_invoice = int(annual_invoice_str)
        except ValueError:
            invoice_map = {
                "50万以下": 250000,
                "50-200万": 1250000,
                "200-500万": 3500000,
                "500-1000万": 7500000,
                "1000万以上": 15000000,
            }
            annual_invoice = invoice_map.get(annual_invoice_str, 0)

    # 2) 兜底：按 income + invoice label 估算
    if annual_invoice == 0:
        invoice_label = data.get("invoice", "")
        mult_map = {"高": 60, "中": 36, "低": 18}  # 5/3/1.5 倍月收入 × 12
        mult = mult_map.get(invoice_label, 0)
        if mult > 0:
            income = income_value(data.get("monthly_income", ""))
            if income > 0:
                annual_invoice = int(income * mult)

    if level == "E" or annual_invoice == 0:
        return 0, 0, 0, 0
    rate = {"S": 0.10, "A": 0.08, "B": 0.06, "C": 0.04, "D": 0.02}.get(level, 0.05)
    chosen = int(annual_invoice * rate)
    if chosen == 0:
        return 0, 0, 0, 0
    limit_min = int(chosen * 0.85)
    limit_max = int(chosen * 1.15)
    return limit_min, limit_max, 6.0, 12.0


# 公式注册表（key = product_types.limit_formula）
LIMIT_FORMULA_REGISTRY = {
    "quality_unit_income": _calc_limit_quality_unit,
    "housing_fund_mult": _calc_limit_housing_fund,
    "salary_income": _calc_limit_salary,
    "house_asset": _calc_limit_house_owner,
    "tax_mult": _calc_limit_tax,
    "invoice_pct": _calc_limit_invoice,
}


# ============================================================================
# 单产品评分流程
# ============================================================================


async def _evaluate_one_product(
    product: ProductType, input_data: dict, type_: str, db: AsyncSession, bank_code: str | None = None
) -> ProductResult:
    """对单个产品跑完整评分流程

    v7 增量：bank_code 不为 None 时按银行 focus 调整 score
    """
    # 1. 加载该产品的规则（通用 + 专属）
    rules = await _load_rules_for_product(type_, db, product.id)

    # 2. 一票否决（互联网银行 veto_relax：一票否决条件更松）
    veto = _check_veto(rules, input_data)
    if veto and bank_code and _is_veto_relax(bank_code):
        # 互联网银行允许「轻度逾期+其他资质好」通过
        credit_overdue = input_data.get("credit_overdue", 0)
        if isinstance(credit_overdue, (int, float)) and credit_overdue <= 2:
            logger.info(f"[bank_bias] {bank_code} veto_relax: 轻度逾期({credit_overdue}) 忽略否决")
            veto = None
    if veto:
        # 命中否决：本产品 E 级，但其他产品可能仍可申请
        veto_msg = veto.get('message', '不符合准入条件')
        return ProductResult(
            product_code=product.code,
            product_name=product.name,
            product_subtitle=product.subtitle or "",
            score=0,
            level="E",
            raw_score=0.0,
            limit_min=0,
            limit_max=0,
            rate_min=RATE_MIN_BY_LEVEL["E"],
            rate_max=RATE_MAX_BY_LEVEL["E"],
            pd=0.85,
            pass_probability="极低",
            formula_used=product.limit_formula,
            focus_vars=product.focus_vars or [],
            key_points=product.key_points or [],
            matched_items=[],
            risk_tags=[f"一票否决：{veto_msg}"],
            advantages=[],
            weak_points=["存在硬性风险项，需先解决"],
            recommend=0,
            description=product.description or "",
            veto=veto,
            # v9 增量：veto 时只填不推荐原因，其他留空（无命中规则 + 实际额度 0）
            not_recommend_reason=f"命中一票否决：{veto_msg}，建议先解决风险项",
            realistic_limit_min=0,
            realistic_limit_max=0,
        )

    # 3. 逐项打分
    raw, items = _score_items(rules, input_data)

    # 4. 归一化 + 等级
    score = _normalize(raw, items)
    # v7 增量：银行差异化加权（ICBC 公积金+1.5x、CCB 房产+1.6x 等）
    if bank_code and score > 0:
        biased = _apply_bank_bias(score, bank_code, product.code)
        if biased != score:
            logger.info(f"[bank_bias] {bank_code} {product.code}: {score:.1f} -> {biased:.1f}")
            score = biased
    level = _level_of(score)

    # 5. 额度公式（按 product.limit_formula 选函数）
    formula_func = LIMIT_FORMULA_REGISTRY.get(product.limit_formula)
    if formula_func:
        limit_min, limit_max, rate_min, rate_max = formula_func(input_data, level)
    else:
        # 未找到公式：兜底用通用 4 方法取最小
        from app.services.scorecard_engine import _calc_limits
        limit_min, limit_max, rate_min, rate_max = _calc_limits(input_data, level)
        formula_func_name = "_calc_limits"
    formula_used = product.limit_formula if formula_func else "_calc_limits"

    # 6. PD + 通过概率
    pd, pass_prob = _calc_pd_and_pass(score, level)

    # 7. 标签（重点变量优先展示）
    risks, advs, weaks = _build_tags(input_data, items)

    # 7.5 P2 渠道合规 cap：把测算额度按线上/线下硬上限截断
    #   解决「用户填的数值好 → 测算值远超银行能给的最高额度」问题
    caps = CHANNEL_CAPS.get(product.code, {})
    online_cap = caps.get("online", 0)
    offline_cap = caps.get("offline", 0)
    limit_min_capped, limit_max_capped, was_capped, reason = apply_channel_cap(
        product.code, limit_min, limit_max
    )
    if was_capped:
        logger.info(
            f"[channel_cap] product={product.code} level={level} "
            f"raw=[{limit_min/10000:.1f}万 ~ {limit_max/10000:.1f}万] → "
            f"capped=[{limit_min_capped/10000:.1f}万 ~ {limit_max_capped/10000:.1f}万]"
        )

    # v9 增量：构建 6 产品独立证据链（命中规则/不推荐原因/提分变量/实际可贷金额）
    evidence = _build_evidence(
        items, rules, score, level, limit_min_capped, limit_max_capped
    )

    return ProductResult(
        product_code=product.code,
        product_name=product.name,
        product_subtitle=product.subtitle or "",
        score=score,
        level=level,
        raw_score=raw,
        limit_min=limit_min_capped,
        limit_max=limit_max_capped,
        rate_min=rate_min,
        rate_max=rate_max,
        pd=pd,
        pass_probability=pass_prob,
        formula_used=formula_used,
        focus_vars=product.focus_vars or [],
        key_points=product.key_points or [],
        matched_items=items,
        risk_tags=risks,
        advantages=advs,
        weak_points=weaks,
        recommend=product.recommend,
        description=product.description or "",
        channel_online_max=online_cap,
        channel_offline_max=offline_cap,
        limit_capped=was_capped,
        limit_reason=reason,
        # v9 增量字段（来自 _build_evidence）
        **evidence,
    )


def _calc_pd_and_pass(score: int, level: str) -> tuple[float, str]:
    """PD 违约概率 → 通过概率（与原引擎一致，k 同步调陡）"""
    if level == "E":
        return 0.85, "极低"
    midpoint = 50.0
    k = 0.12
    pd = 1.0 / (1.0 + math.exp(k * (score - midpoint)))
    for thr, label in PASS_PROB_MAP:
        if pd <= thr:
            return pd, label
    return pd, "极低"


# 通过概率排序权重（用于"最匹配该用户"的产品挑选）
_PASS_PROB_RANK: dict[str, int] = {
    "高": 5,
    "中高": 4,
    "中": 3,
    "低": 2,
    "极低": 1,
}


def _mark_best_for_user(results: list[ProductResult]) -> None:
    """
    从 6 个产品里挑出"对当前用户最合适"的那 1 个，置 best_for_user=True。
    其余置 False（默认）。

    排除规则（直接出局）：
      - level == "E"（一票否决或异常）
      - pass_probability == "极低"

    挑选优先级：
      1. 通过概率最高（高 > 中高 > 中 > 低）
      2. 同级：score 最高
      3. 再同：DB 标志 recommend=1 的产品（产品维度的营销推荐）
      4. 再同：matched_items 数量最多

    若所有产品都被排除 → 不打任何 ⭐（报告页不显示"推荐"标签）
    """
    # 0. 清空所有
    for r in results:
        r.best_for_user = False

    # 1. 候选
    candidates = [
        r for r in results
        if r.level != "E" and r.pass_probability != "极低"
    ]
    if not candidates:
        return

    # 2. 多级排序
    #    通过概率 > DB 标志权重(10) > score > 命中规则数
    #    注意 recommend 权重 ×10，让"主推产品"在 score 差距 <10 时优先
    candidates.sort(
        key=lambda r: (
            _PASS_PROB_RANK.get(r.pass_probability, 0),  # 通过概率等级
            r.recommend * 10,                            # DB 标志主推（权重 10）
            r.score,                                     # 综合分
            len(r.matched_items),                        # 命中规则数
        ),
        reverse=True,
    )
    candidates[0].best_for_user = True


# ============================================================================
# 主入口：6 大产品独立测算
# ============================================================================


async def calculate_scores_by_product(
    input_data: dict,
    type_: str,
    db: AsyncSession,
    bank_code: str | None = None,
) -> list[ProductResult]:
    """
    6 大产品独立测算主入口

    1. 加载所有启用的产品类型（按 user_type 匹配 + sort_order 排序）
    2. 对每个产品跑 _evaluate_one_product
    3. 返回 ProductResult 列表

    参数：
      input_data: 用户填写的 23 字段
      type_: personal / business
      db: AsyncSession
      bank_code: 银行 code（v7 增量，按银行 focus 调整评分；None = 通用模型）

    返回：
      list[ProductResult]，按 sort_order 排序
    """
    # 1. 加载产品类型
    stmt = (
        select(ProductType)
        .where(
            ProductType.enabled == True,  # noqa: E712
        )
        .order_by(ProductType.sort_order.asc())
    )
    res = await db.execute(stmt)
    all_products = res.scalars().all()
    # 2. 按 user_type 过滤
    matched = [p for p in all_products if p.user_type == type_]
    if not matched:
        logger.warning(f"没有匹配 user_type={type_} 的产品配置")
        return []

    # 3. 对每个产品跑独立评分
    results: list[ProductResult] = []
    for product in matched:
        try:
            r = await _evaluate_one_product(product, input_data, type_, db, bank_code)
            results.append(r)
        except Exception as e:
            logger.error(f"产品 {product.code} 测算失败: {e}")
            # 失败也给个兜底结果
            results.append(ProductResult(
                product_code=product.code,
                product_name=product.name,
                product_subtitle=product.subtitle or "",
                score=0,
                level="E",
                raw_score=0.0,
                limit_min=0,
                limit_max=0,
                rate_min=RATE_MIN_BY_LEVEL["E"],
                rate_max=RATE_MAX_BY_LEVEL["E"],
                pd=0.85,
                pass_probability="极低",
                formula_used=product.limit_formula,
                focus_vars=product.focus_vars or [],
                key_points=product.key_points or [],
                matched_items=[],
                risk_tags=["测算异常"],
                advantages=[],
                weak_points=[],
                recommend=0,
                description=product.description or "",
                not_recommend_reason="测算异常，请稍后再试",
            ))

    # 4. 从 6 个产品中挑出"最适合当前用户"的那 1 个打 best_for_user=True
    #    用于报告页 ⭐ 标签：避免"⭐ + 通过率极低"这种自相矛盾
    _mark_best_for_user(results)

    return results


def synthesize_overall_score(results: list[ProductResult]) -> tuple[int, str, int, int, float, float, str]:
    """
    综合分 = 6 套产品分数的加权平均（推荐产品权重 ×1.5，其他 ×1.0）

    返回：(score, level, limit_min, limit_max, rate_min, rate_max, pass_probability)
    """
    if not results:
        return 0, "E", 0, 0, 0, 0, "极低"

    # 过滤掉 veto 的（level=E 且有 veto 字段）
    valid = [r for r in results if r.veto is None]
    if not valid:
        return 0, "E", 0, 0, 0, 0, "极低"

    # 加权
    total_weight = 0.0
    weighted_score = 0.0
    limit_mins: list[int] = []
    limit_maxs: list[int] = []
    rate_mins: list[float] = []
    rate_maxs: list[float] = []
    pass_probs: list[str] = []

    for r in valid:
        w = 1.5 if r.recommend else 1.0
        weighted_score += r.score * w
        total_weight += w
        if r.limit_min > 0:
            limit_mins.append(r.limit_min)
            limit_maxs.append(r.limit_max)
            rate_mins.append(r.rate_min)
            rate_maxs.append(r.rate_max)
            pass_probs.append(r.pass_probability)

    overall_score = int(round(weighted_score / total_weight)) if total_weight > 0 else 0
    overall_level = _level_of(overall_score)

    # 综合额度 = 各产品额度的中位数（避免被极端值拉偏）
    if limit_mins:
        limit_mins.sort()
        limit_maxs.sort()
        rate_mins.sort()
        rate_maxs.sort()
        n = len(limit_mins)
        median_min = limit_mins[n // 2]
        median_max = limit_maxs[n // 2]
        median_rate_min = rate_mins[n // 2]
        median_rate_max = rate_maxs[n // 2]
        # 通过概率取众数（最常出现的等级）
        from collections import Counter
        most_common = Counter(pass_probs).most_common(1)
        overall_pass = most_common[0][0] if most_common else "中"
    else:
        median_min = median_max = 0
        median_rate_min = median_rate_max = 0
        overall_pass = "极低"

    # 综合额度按综合分等级折扣（避免"低分高额度"自相矛盾）
    # S/A 维持原值；B 0.5（中等客群实际授信 50% 折扣）；C 0.3；D 0.15；E 0（拒批）
    # 旧值 B=0.7/C=0.5/D=0.3 偏乐观，对应"测算额度虚高"问题
    # v9 增量：改用模块级 _LIMIT_DISCOUNT（与 _build_evidence 共用同一份配置）
    discount = _LIMIT_DISCOUNT.get(overall_level, 0.5)
    final_min = int(round(median_min * discount))
    final_max = int(round(median_max * discount))
    # v7 增量：综合额度也圆整到 5000 整数倍（与各产品一致）
    final_min = _round_to_nice(final_min)
    final_max = _round_to_nice(final_max)

    # E 级 或 D 级且分很低 → 强制低通过率（避免 "D + 极低分" 却显示 "中"）
    if overall_level == "E":
        overall_pass = "极低"
    elif overall_level == "D" and overall_pass in ("高", "中高", "中"):
        overall_pass = "低"

    return (
        overall_score,
        overall_level,
        final_min,
        final_max,
        median_rate_min,
        median_rate_max,
        overall_pass,
    )
