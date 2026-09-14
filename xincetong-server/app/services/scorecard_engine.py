"""
评分卡核心引擎

按银行 A 卡四层逻辑：
  1. 准入层（一票否决）：年龄/逾期/黑户/集中查询 等硬指标
  2. 反欺诈层：预留（阶段 6 接入）
  3. A 卡层：基于 5 大类变量打分（基础/职业/收入/资产/征信）
  4. 额度/利率层：4 种额度测算方法取最小值

评分流程：
  加载规则 → 一票否决 → 逐项打分 → 归一化 0~100 → 等级映射
  → 额度测算（4 方法）→ PD 违约概率 → 通过概率
  → 风险标签 / 优势 / 弱点

核心原则：
  - 评分规则全走 scorecard_rules 表（不硬编码）
  - 一票否决单独判断，不进入评分
  - 4 种额度测算方法取最小值
  - 通过概率基于 PD 违约概率映射
  - 接口返回统一 {code, message, data} 格式
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scorecard import ScorecardRule
from app.utils.logger import logger
from app.utils.money import (
    car_value,
    housing_fund_value,
    house_value,
    income_value,
    min_of,
    monthly_debt_value,
)
from app.utils.redis_client_safe import cache_get, cache_set  # 缓存（带安全降级）

# ============================================================================
# 常量配置
# ============================================================================

# 等级映射（分数 → 等级）
LEVEL_THRESHOLDS: list[tuple[int, str]] = [
    (80, "S"),
    (70, "A"),
    (55, "B"),
    (40, "C"),
    (20, "D"),
    (0, "E"),
]

# 通过概率等级（按 PD 区间映射）
PASS_PROB_MAP: list[tuple[float, str]] = [
    (0.05, "高"),
    (0.15, "中高"),
    (0.30, "中"),
    (0.50, "低"),
    (1.01, "极低"),
]

# 等级 → 利率区间下限（年化 %）
RATE_MIN_BY_LEVEL: dict[str, float] = {
    "S": 3.5, "A": 4.5, "B": 6.0, "C": 8.5, "D": 12.0, "E": 18.0,
}
# 等级 → 利率区间上限
RATE_MAX_BY_LEVEL: dict[str, float] = {
    "S": 5.0, "A": 7.0, "B": 9.5, "C": 14.0, "D": 18.0, "E": 24.0,
}

# 等级 → 收入倍数法（年）
# 银行 2025 实际参考：
#   优质客群(公务员/事业/代发) 4-8 倍；普通工薪 2-4 倍；弱客群 1-2 倍；E 级拒批
INCOME_MULTIPLIER: dict[str, int] = {
    "S": 6, "A": 5, "B": 4, "C": 2, "D": 1, "E": 0,
}
# 等级 → 公积金倍数法（基于月缴×12）
# 银行实操：月缴存 × 100-200 倍；弱客群 24-60 倍
HOUSING_FUND_MULTIPLIER: dict[str, int] = {
    "S": 200, "A": 150, "B": 100, "C": 60, "D": 24, "E": 0,
}
# 等级 → 资产抵押率（房价的百分比）
# D/E 收紧：D=0.15（银行实际最多给 30% 抵押，对较弱客群降到 15%）、E=0
ASSET_MORTGAGE_RATE: dict[str, float] = {
    "S": 0.7, "A": 0.6, "B": 0.5, "C": 0.4, "D": 0.15, "E": 0.0,
}

# DSR（偿债比率）阈值：月还款 / 月收入 应 ≤ 0.5
DSR_THRESHOLD = 0.5
# 默认贷款期数
DEFAULT_TERM_MONTHS = 36

# 风险标签 / 优势 / 弱点的硬编码描述（标签库，可后续抽到 DB）
RISK_TAGS: list[tuple[str, str, str]] = [
    # (key, level, text)  level: risk / advantage / weak
    ("credit_usage_high",    "risk",      "信用卡使用率偏高"),
    ("query_too_many",       "risk",      "近 3 个月查询次数过多"),
    ("overdue_2year",        "risk",      "近 2 年存在逾期"),
    ("serial_overdue",       "risk",      "存在连续逾期"),
    ("current_overdue",      "risk",      "当前有逾期"),
    ("white_account",        "risk",      "存在白户风险"),
    ("bad_status",           "risk",      "存在次级/可疑/损失账户"),
    ("loan_too_many",        "risk",      "在贷笔数偏多"),
    ("housing_fund",         "advantage", "公积金连续缴存"),
    ("house_owned",          "advantage", "本地有房产"),
    ("car_owned",            "advantage", "名下有车辆"),
    ("social_security",      "advantage", "社保连续缴存"),
    ("payroll",              "advantage", "工资代发"),
    ("gov_unit",             "advantage", "优质单位背景"),
    ("credit_usage_low",     "advantage", "信用卡使用率低"),
    ("no_overdue",           "advantage", "近 2 年无逾期"),
    ("house_no_mortgage",    "advantage", "无按揭"),
    ("income_low",           "weak",      "月收入偏低"),
    ("work_short",           "weak",      "工作年限较短"),
    ("loan_balance_high",    "weak",      "已有贷款余额偏高"),
]


# ============================================================================
# 数据类
# ============================================================================


@dataclass
class ScoreResult:
    """评分结果"""

    score: int
    level: str
    raw_score: float
    matched_items: list[dict[str, Any]] = field(default_factory=list)
    veto: dict[str, Any] | None = None
    limit_min: int = 0
    limit_max: int = 0
    rate_min: float = 0.0
    rate_max: float = 0.0
    pd: float = 0.0
    pass_probability: str = "极低"
    risk_tags: list[str] = field(default_factory=list)
    advantages: list[str] = field(default_factory=list)
    weak_points: list[str] = field(default_factory=list)
    suggestions: list[dict[str, str]] = field(default_factory=list)
    products: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "level": self.level,
            "raw_score": round(self.raw_score, 2),
            "matched_items": self.matched_items,
            "veto": self.veto,
            "limit_min": self.limit_min,
            "limit_max": self.limit_max,
            "rate_min": self.rate_min,
            "rate_max": self.rate_max,
            "pd": round(self.pd, 4),
            "pass_probability": self.pass_probability,
            "risk_tags": self.risk_tags,
            "advantages": self.advantages,
            "weak_points": self.weak_points,
            "suggestions": self.suggestions,
            "products": self.products,
        }


# ============================================================================
# 规则加载（Redis 缓存 + DB 兜底）
# ============================================================================


_CACHE_KEY = "scorecard:rules:v1"  # 通用规则缓存 key
_CACHE_TTL = 600  # 10 分钟


async def _load_rules(
    type_: str, db: AsyncSession, bank_id: int | None = None
) -> list[dict]:
    """
    从缓存加载规则，缓存未命中走 DB，回写缓存

    多银行规则策略：
    - 加载 bank_id = NULL 的「通用规则」（适用于所有银行）
    - 加载 bank_id = 指定值的「银行专属规则」
    - 合并后按 sort_order 排序
    - 银行专属规则覆盖通用规则（同 variable + option_label 时）
    """
    # 缓存按 bank_id 区分 key
    cache_key = f"scorecard:rules:v1:bank_{bank_id or 'common'}"
    cached = await cache_get(cache_key)
    if cached:
        try:
            return [r for r in json.loads(cached) if r.get("enabled") and r.get("type") in (type_, "both")]
        except Exception as e:
            logger.warning(f"scorecard: 缓存反序列化失败 {e}")

    # 加载「通用规则 + 银行专属规则」
    if bank_id is None:
        bank_filter = ScorecardRule.bank_id.is_(None)
    else:
        # SQL 的 IN 不处理 NULL，要 OR bank_id IS NULL
        from sqlalchemy import or_
        bank_filter = or_(ScorecardRule.bank_id.is_(None), ScorecardRule.bank_id == bank_id)
    stmt = select(ScorecardRule).where(
        ScorecardRule.enabled == 1,
        bank_filter,
    )
    res = await db.execute(stmt)
    rows = res.scalars().all()
    data = [
        {
            "bank_id": r.bank_id,
            "category": r.category,
            "variable": r.variable,
            "option_label": r.option_label,
            "score": float(r.score),
            "type": r.type,
            "is_veto": r.is_veto,
            "sort_order": r.sort_order,
            "enabled": r.enabled,
        }
        for r in rows
    ]
    # 写缓存
    try:
        await cache_set(cache_key, json.dumps(data, ensure_ascii=False), _CACHE_TTL)
    except Exception as e:
        logger.warning(f"scorecard: 缓存写失败 {e}")

    return [r for r in data if r.get("type") in (type_, "both")]


# ============================================================================
# 一票否决
# ============================================================================


def _check_veto(rules: list[dict], data: dict) -> dict | None:
    """检查一票否决项，命中返回 {rule, message, level}"""
    for r in rules:
        if r.get("is_veto") != 1:
            continue
        var = r["variable"]
        if _norm(data.get(var)) == _norm(r["option_label"]) and data.get(var) is not None:
            return {
                "rule_variable": var,
                "rule_label": r["option_label"],
                "category": r.get("category"),
                "message": f"{_var_zh(var)}：{r['option_label']} 不符合准入条件",
            }
    return None


def _var_zh(var: str) -> str:
    """变量名 → 中文显示名（用户看的一票否决消息、focus_vars 介绍等都用此映射）"""
    return {
        # 个人
        "age": "年龄",
        "current_overdue": "当前逾期",
        "serial_overdue": "连续逾期",
        "bad_status": "账户状态",
        "white_account": "白户风险",
        "id_card_check": "实名认证",
        "overdue_2year": "近 2 年逾期",
        "recent_3month_queries": "近 3 个月查询",
        "credit_card_usage": "信用卡使用率",
        "credit_card_count": "信用卡张数",
        "loan_count": "在贷笔数",
        "monthly_income": "月收入",
        "monthly_debt": "月负债",
        "social_security": "社保",
        "housing_fund": "公积金",
        "company_type": "单位类型",
        "work_years": "工龄",
        "payroll": "代发工资",
        "education": "学历",
        "marriage": "婚姻状况",
        "city_tier": "城市等级",
        "house": "房产",
        "car": "车辆",
        "deposit": "存款",
        "insurance": "商业保险",
        # 企业（v4 P0 补全）
        "tax_grade": "纳税等级",
        "annual_tax": "年纳税额",
        "tax_continuity": "纳税连续性",
        "business_years": "经营年限",
        "annual_invoice": "年开票额",
        "invoice_continuity": "开票连续性",
        "industry": "所属行业",
        # 企业（v5 P0 补全：8 新变量 + 一票否决）
        "legal_form": "组织形式",
        "legal_holding": "法人持股",
        "employee_count": "参保人数",
        "biz_balance": "对公日均余额",
        "biz_loan_count": "对公贷款笔数",
        "biz_overdue_2y": "对公近 2 年逾期",
        "biz_query_3m": "对公近 3 月查询",
        "compliance_risk": "合规风险",
    }.get(var, var)


# ============================================================================
# 逐项打分
# ============================================================================


def _norm(s) -> str:
    """规范化匹配串：去空格、全角转半角、转小写（解决前端"31-40 岁" vs 规则"31-40岁"不一致）"""
    if s is None:
        return ""
    return str(s).replace(" ", "").replace("　", "").lower()


def _score_items(rules: list[dict], data: dict) -> tuple[float, list[dict]]:
    """遍历规则，按 variable+option_label 匹配，返回 (raw_score, items)

    匹配采用"规范化比对"（去空格、转小写），避免前端"31-40 岁" vs 规则"31-40岁"的不一致 bug。
    """
    items: list[dict] = []
    raw = 0.0
    for r in rules:
        if r.get("is_veto") == 1:
            continue
        var = r["variable"]
        if _norm(data.get(var)) == _norm(r["option_label"]) and data.get(var) is not None:
            raw += float(r["score"])
            items.append(
                {
                    "category": r.get("category"),
                    "variable": var,
                    "option_label": r["option_label"],
                    "score": float(r["score"]),
                }
            )
    return raw, items


# ============================================================================
# 归一化 + 等级
# ============================================================================


def _normalize(raw: float, items: list[dict]) -> int:
    """
    归一化到 0~100。

    评分规则全表实际命中满分为 ~174 分（基础 22 + 职业 52 + 收入 30 + 资产 40 + 征信 50
    中通常会同时命中的高分项累计；取实际可能命中的最大经验值）。
    原 /2.0 是按"全 200 分对半"的旧估算，导致全优用户只到 87 分，整体偏低。
    改 /1.74 后，全优用户命中 ~170 → 归一化到 98 分，更符合"满分 100"的预期。
    """
    if not items:
        return 0
    return max(0, min(100, int(round(raw * 100 / 174))))


def _level_of(score: int) -> str:
    for thr, lv in LEVEL_THRESHOLDS:
        if score >= thr:
            return lv
    return "E"


# ============================================================================
# 额度测算（4 种方法取最小）
# ============================================================================


def _calc_limits(data: dict, level: str) -> tuple[int, int, float, float]:
    """
    4 种额度测算方法，取最小：
      1. 收入倍数法：月收入 × 12 × INCOME_MULTIPLIER
      2. 公积金倍数法：月公积金 × 12 × HOUSING_FUND_MULTIPLIER
      3. 资产法：(房价 - 已有按揭 + 车价) × ASSET_MORTGAGE_RATE
      4. DSR 约束：(月收入 - 月还款) / 月收入 ≤ 0.5 → 反算最大月还款 → 36 期反算额度
    """
    if level == "E":
        return 0, 0, RATE_MIN_BY_LEVEL["E"], RATE_MAX_BY_LEVEL["E"]

    income = income_value(data.get("monthly_income", ""))
    fund = housing_fund_value(data.get("housing_fund", ""))
    house = house_value(data.get("house", ""))
    car = car_value(data.get("car", ""))
    monthly_debt = monthly_debt_value(data.get("monthly_debt", "") or "无")

    # 1. 收入倍数法（年收入 × 倍数）
    annual_income = income * 12
    limit_income = annual_income * INCOME_MULTIPLIER.get(level, 0)

    # 2. 公积金倍数法
    limit_fund = fund * 12 * HOUSING_FUND_MULTIPLIER.get(level, 0)

    # 3. 资产法（净值 = 评估价 - 估算按揭余额）
    # 银行内部模型应扣减按揭余额（净值=可二次抵押价值）。
    # 我们用粗估：无按揭=全额评估价；高净值率(0.6)假设已还 40%；
    # 弱客群按 D=0.4 净值率（按揭比例往往更高）。
    _NET_RATIO = {"S": 0.85, "A": 0.75, "B": 0.65, "C": 0.55, "D": 0.4, "E": 0.0}
    net_ratio = _NET_RATIO.get(level, 0.5)
    house_net = house if data.get("house") == "无按揭" else house * net_ratio
    asset_value = house_net + car
    limit_asset = asset_value * ASSET_MORTGAGE_RATE.get(level, 0)

    # 4. DSR 约束：最大月还款 = (月收入 - 月负债) × 0.5
    available_monthly = max(0, (income - monthly_debt)) * DSR_THRESHOLD
    # 按当前等级中位利率 / 36 期反算
    rate_pct = (RATE_MIN_BY_LEVEL.get(level, 0) + RATE_MAX_BY_LEVEL.get(level, 0)) / 2 / 100
    monthly_rate = rate_pct / 12
    n = DEFAULT_TERM_MONTHS
    if available_monthly > 0 and monthly_rate > 0:
        # 等额本息公式反算：本金 = 月供 × (1 - (1+r)^-n) / r
        limit_dsr = available_monthly * (1 - (1 + monthly_rate) ** (-n)) / monthly_rate
    else:
        limit_dsr = 0

    candidates = [limit_income, limit_fund, limit_asset, limit_dsr]
    chosen = min_of(candidates)

    # 上下区间（下界 = 0.85 倍，上界 = 1.15 倍）
    # 原 ±30% 让用户感觉"虚高"，银行实际模型 ±10-15% 较合理
    limit_min = int(chosen * 0.85)
    limit_max = int(chosen * 1.15)

    # P3-4 DSR 约束：新贷款月供 + 已有月供 / 月收入 ≤ 0.5
    # chosen × 1.15 后实际 DSR 会 = 0.5 × 1.15 = 0.575（超 0.5 上限）
    # 因此 limit_max 不能超过 DSR 反算的"刚到 0.5 上限"那个精确本金
    # 解决"用户能承受月供 X，但报告推的额度导致月供 Y > X"问题
    if limit_dsr > 0 and limit_max > limit_dsr:
        # 实际新贷款月供（含已有月供）：用 limit_dsr 反算的月供 = available_monthly
        # limit_dsr 时 DSR = 0.5；超过 limit_dsr 时 DSR > 0.5
        # → 把 limit_max 截到 limit_dsr，确保 DSR 严格 ≤ 0.5
        old_limit_max = limit_max
        limit_max = int(limit_dsr)
        import logging
        logging.getLogger(__name__).info(
            f"[dsr_cap] chosen={chosen/10000:.1f}万 raw_max={old_limit_max/10000:.1f}万 "
            f"dsr_exact={limit_dsr/10000:.1f}万 → cap limit_max to {limit_max/10000:.1f}万 "
            f"(DSR 上限 0.5，1.15 倍放大后月供 = {old_limit_max/limit_dsr*0.5:.3f} 月收入，超标)"
        )

    # E 级返回 0 额度
    if level == "E":
        limit_min, limit_max = 0, 0

    # P2 渠道合规 cap：综合额度（个人无抵押消费贷）按"线下最高 100 万"截断
    # 银保监 2020/7 文：单户消费贷 ≤ 30 万（互联网贷款）；线下商业银行自营 ≤ 100 万
    # 解决"用户填的数值好" → 测算值远超银行能给的最高额度 问题
    OFFLINE_LIMIT_CAP = 100_0000  # 100 万
    if limit_max > OFFLINE_LIMIT_CAP:
        scale = OFFLINE_LIMIT_CAP / limit_max if limit_max > 0 else 1.0
        limit_min = int(limit_min * scale)
        limit_max = int(limit_max * scale)

    return (
        limit_min,
        limit_max,
        RATE_MIN_BY_LEVEL[level],
        RATE_MAX_BY_LEVEL[level],
    )


# ============================================================================
# PD 违约概率 → 通过概率
# ============================================================================


def _calc_pd_and_pass(score: int, level: str) -> tuple[float, str]:
    """
    PD = 1 / (1 + exp(k * (score - midpoint)))
    midpoint = 50（评分中位）
    k = 0.12（原 0.08，斜率过缓导致 80 分的 S 级只能拿"中高"通过率）
    调整后各档位预期通过率：
      score=80 → PD≈0.027 → "高"
      score=70 → PD≈0.083 → "中高"
      score=60 → PD≈0.231 → "中"
      score=50 → PD≈0.500 → "低"
      score=40 → PD≈0.768 → "极低"
    """
    if level == "E":
        return 0.85, "极低"
    midpoint = 50.0
    k = 0.12
    pd = 1.0 / (1.0 + math.exp(k * (score - midpoint)))
    for thr, label in PASS_PROB_MAP:
        if pd <= thr:
            return pd, label
    return pd, "极低"


# ============================================================================
# 风险标签 / 优势 / 弱点
# ============================================================================


def _build_tags(data: dict, items: list[dict]) -> tuple[list[str], list[str], list[str]]:
    """根据用户数据匹配标签库"""
    risks: list[str] = []
    advs: list[str] = []
    weaks: list[str] = []

    def has(var: str, val: str) -> bool:
        return data.get(var) == val

    def in_(var: str, vals: list[str]) -> bool:
        return data.get(var) in vals

    if has("current_overdue", "有"):
        risks.append("当前有逾期")
    if has("serial_overdue", "有"):
        risks.append("存在连续逾期")
    if has("overdue_2year", "3次以上"):
        risks.append("近 2 年逾期 3 次以上")
    if has("overdue_2year", "1-3次"):
        risks.append("近 2 年有逾期")
    if has("white_account", "是"):
        risks.append("白户风险（无信贷记录）")
    if has("bad_status", "有"):
        risks.append("账户存在次级/可疑/损失")
    if in_("credit_card_usage", ["80%以上"]):
        risks.append("信用卡使用率过高")
    if in_("recent_3month_queries", ["6次以上"]):
        risks.append("近 3 个月查询过多")
    if in_("loan_count", ["5笔以上"]):
        risks.append("在贷笔数偏多")

    if in_("social_security", ["连续1-3年", "连续3年以上", "连续 1-3 年", "连续 3 年以上"]):
        advs.append("社保连续缴存")
    if has("housing_fund", "正常基数") or has("housing_fund", "高基数"):
        advs.append("公积金连续缴存")
    if has("payroll", "是"):
        advs.append("工资代发")
    if in_("company_type", ["公务员/事业单位", "国企/央企", "上市公司"]):
        advs.append("优质单位背景")
    if has("house", "无按揭"):
        advs.append("本地有房无按揭")
    if has("car", "10-30万") or has("car", "30万以上"):
        advs.append("名下有车")
    if has("overdue_2year", "0次"):
        advs.append("近 2 年无逾期")
    if has("credit_card_usage", "30%以下"):
        advs.append("信用卡使用率低")

    if in_("monthly_income", ["5000以下"]):
        weaks.append("月收入偏低")
    if in_("work_years", ["1年以下"]):
        weaks.append("工作年限较短")
    if in_("loan_count", ["3-5笔", "5笔以上"]):
        weaks.append("已有贷款笔数较多")
    if has("credit_card_usage", "80%以上"):
        weaks.append("信用卡额度占用高")

    return risks, advs, weaks


# ============================================================================
# 改善建议
# ============================================================================


def _build_suggestions(data: dict, level: str, risks: list[str]) -> list[dict[str, str]]:
    """根据等级和风险标签生成改善建议"""
    suggestions: list[dict[str, str]] = []

    if level in ("D", "E"):
        suggestions.append({"period": "立即", "action": "暂缓申请任何贷款，先解决逾期 / 高负债问题"})

    if "当前有逾期" in risks:
        suggestions.append({"period": "1-3 个月", "action": "结清当前逾期，让征信更新"})

    if "近 3 个月查询过多" in risks:
        suggestions.append({"period": "3-6 个月", "action": "停止申请新贷款 / 信用卡，3 个月后再申请"})

    if "信用卡使用率过高" in risks or "信用卡额度占用高" in risks:
        suggestions.append({"period": "1-2 个月", "action": "还一部分信用卡，降低使用率到 50% 以下"})

    if "白户风险（无信贷记录）" in risks:
        suggestions.append({"period": "3-6 个月", "action": "先申请 1 张信用卡并正常使用，建立信用记录"})

    # 兼容 "5000以下" 和 "5000 以下" 两种 label（前端去空格+后端空格）
    _monthly = (data.get("monthly_income") or "").replace(" ", "")
    if level in ("C", "B") and _monthly == "5000以下":
        suggestions.append({"period": "3-6 个月", "action": "提升收入流水（兼职、副业等）"})

    if level in ("B", "A"):
        suggestions.append({"period": "1-3 个月", "action": "可申请 1-2 家银行信贷，避免短期内多头申请"})

    if level == "A":
        suggestions.append({"period": "1-3 个月", "action": "优先申请公积金 / 工资代发银行的低息产品"})

    if level == "S":
        suggestions.append({"period": "立即", "action": "可同时申请 2-3 家银行优选产品，择优放款"})

    # 兜底建议
    if not suggestions:
        suggestions.append({"period": "持续", "action": "保持良好信用习惯，按时还款"})

    return suggestions


# ============================================================================
# 推荐产品（按等级匹配 + 风险过滤）
# ============================================================================


def _build_products(level: str, limit_min: int, limit_max: int, rate_min: float, rate_max: float) -> list[dict]:
    """
    根据等级匹配 3-5 个虚拟产品。
    通过概率按等级映射：高(S/A) > 中高(B) > 中(C) > 低(D) > 极低(E)
    """
    products_by_level: dict[str, list[dict]] = {
        "S": [
            {"name": "公积金优享贷",    "rate_lo": 3.50, "rate_hi": 4.50, "pass": "高",   "recommend": True},
            {"name": "工资代发极速贷",  "rate_lo": 3.80, "rate_hi": 5.20, "pass": "高"},
            {"name": "白领信用贷",      "rate_lo": 4.20, "rate_hi": 6.00, "pass": "高"},
        ],
        "A": [
            {"name": "公积金优享贷",    "rate_lo": 4.20, "rate_hi": 6.00, "pass": "高",   "recommend": True},
            {"name": "工资代发极速贷",  "rate_lo": 4.50, "rate_hi": 6.50, "pass": "中高"},
            {"name": "白领信用贷",      "rate_lo": 5.00, "rate_hi": 7.50, "pass": "中高"},
            {"name": "车主贷",          "rate_lo": 6.00, "rate_hi": 9.00, "pass": "中"},
        ],
        "B": [
            {"name": "工薪贷",          "rate_lo": 6.50, "rate_hi": 9.50, "pass": "中高", "recommend": True},
            {"name": "公积金贷",        "rate_lo": 7.00, "rate_hi": 10.0, "pass": "中"},
            {"name": "保单贷",          "rate_lo": 8.00, "rate_hi": 12.0, "pass": "中"},
        ],
        "C": [
            {"name": "消费分期",        "rate_lo": 10.0,  "rate_hi": 14.0, "pass": "中",   "recommend": True},
            {"name": "小额信贷",        "rate_lo": 12.0,  "rate_hi": 18.0, "pass": "中"},
            {"name": "信用卡分期",      "rate_lo": 13.0,  "rate_hi": 18.0, "pass": "低"},
        ],
        "D": [
            {"name": "小额信贷",        "rate_lo": 15.0,  "rate_hi": 22.0, "pass": "低",   "recommend": True},
            {"name": "消费分期",        "rate_lo": 18.0,  "rate_hi": 24.0, "pass": "低"},
        ],
        "E": [
            {"name": "暂无可推荐产品",  "rate_lo": 0,     "rate_hi": 0,    "pass": "极低"},
        ],
    }

    raw_list = products_by_level.get(level, products_by_level["E"])
    out: list[dict] = []
    for p in raw_list:
        out.append(
            {
                "name": p["name"],
                "limit": (
                    f"¥{limit_min // 10000}万 ~ ¥{limit_max // 10000}万"
                    if limit_max >= 10000
                    else f"¥{limit_min} ~ ¥{limit_max}"
                ),
                "rate": f"{p['rate_lo']:.2f}% ~ {p['rate_hi']:.2f}%",
                "pass": p["pass"],
                "recommend": p.get("recommend", False),
            }
        )
    return out


# ============================================================================
# 主入口
# ============================================================================


async def calculate_score(
    input_data: dict,
    type_: str = "personal",
    db: AsyncSession | None = None,
    rules: list[dict] | None = None,
    bank_id: int | None = None,
) -> ScoreResult:
    """
    评分卡主入口：
    1. 加载规则（DB 模式自动加载；测试可外部注入）
    2. 一票否决
    3. 逐项打分
    4. 归一化 + 等级
    5. 额度测算
    6. PD → 通过概率
    7. 标签 + 建议 + 产品

    bank_id: 关联银行（None = 通用规则）
    """
    if rules is None:
        if db is None:
            # 既无 DB 也无 rules：返回 B 级兜底
            return _score_with_empty_rules(input_data)
        rules = await _load_rules(type_, db, bank_id=bank_id)

    # 1. 一票否决
    veto = _check_veto(rules, input_data)
    if veto:
        # 命中否决：直接 E 级
        return ScoreResult(
            score=0,
            level="E",
            raw_score=0.0,
            matched_items=[],
            veto=veto,
            limit_min=0,
            limit_max=0,
            rate_min=RATE_MIN_BY_LEVEL["E"],
            rate_max=RATE_MAX_BY_LEVEL["E"],
            pd=0.85,
            pass_probability="极低",
            risk_tags=["一票否决：不符合准入条件"],
            advantages=[],
            weak_points=["存在硬性风险项，需先解决"],
            suggestions=[{"period": "立即", "action": "暂缓申请，解决问题后重试"}],
            products=_build_products("E", 0, 0, 0, 0),
        )

    # 2. 逐项打分
    raw, items = _score_items(rules, input_data)

    # 3. 归一化
    score = _normalize(raw, items)
    level = _level_of(score)

    # 4. 额度测算
    limit_min, limit_max, rate_min, rate_max = _calc_limits(input_data, level)

    # 5. PD + 通过概率
    pd, pass_prob = _calc_pd_and_pass(score, level)

    # 6. 标签
    risks, advs, weaks = _build_tags(input_data, items)

    # 7. 建议
    suggestions = _build_suggestions(input_data, level, risks)

    # 8. 推荐产品
    products = _build_products(level, limit_min, limit_max, rate_min, rate_max)

    return ScoreResult(
        score=score,
        level=level,
        raw_score=raw,
        matched_items=items,
        veto=None,
        limit_min=limit_min,
        limit_max=limit_max,
        rate_min=rate_min,
        rate_max=rate_max,
        pd=pd,
        pass_probability=pass_prob,
        risk_tags=risks,
        advantages=advs,
        weak_points=weaks,
        suggestions=suggestions,
        products=products,
    )


def _score_with_empty_rules(input_data: dict) -> ScoreResult:
    """无规则时：返回 B 级兜底"""
    score = 50
    level = "B"
    limit_min, limit_max, rate_min, rate_max = _calc_limits(input_data, level)
    pd, pass_prob = _calc_pd_and_pass(score, level)
    return ScoreResult(
        score=score,
        level=level,
        raw_score=100.0,
        limit_min=limit_min,
        limit_max=limit_max,
        rate_min=rate_min,
        rate_max=rate_max,
        pd=pd,
        pass_probability=pass_prob,
    )
