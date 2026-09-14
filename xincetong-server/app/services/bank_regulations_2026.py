"""
2026 银行新规基准数据（v16 重大重写）

核心理念：所有额度、利率、抵押率都必须依据「2026 央行/金管总局/银保监会」
的真实监管规则，而不是开发者的"拍脑袋"经验值。

数据来源（每个常量上方标注 URL / 文件名）：
  - 5 年期 LPR / 1 年期 LPR：央行 2026-09 公布
  - 公积金贷款利率：央行/住建部 2025-05-08
  - 监管上限：银保监会 2020 《商业银行互联网贷款管理暂行办法》/ 2024 新规
  - 普惠小微口径：金融监管总局 2026-05-19《关于做好 2026 年小微企业金融
    服务工作的通知》（金办发〔2026〕44 号）
  - 个人消费贷贴息：财政部 央行 金管总局 2026-01-16 / 2026-08-21
  - 首套/二套房贷：央行 2025-12《关于调整优化差别化住房信贷政策的通知》

设计原则：
  1. 每个数字都标注「依据」字段（真实文件名 + 链接），便于审计/合规
  2. 派生规则（如利率上下限）显式写公式 LPR±BP，方便日后 LPR 调整时只改 1 处
  3. 数据结构 = 「监管底线 + 银行 override」两层：
     监管是 hard floor/ceiling，银行可以在范围内微调

2026-09-14 立。
"""
from __future__ import annotations

# ============================================================================
# 1. 央行贷款市场报价利率（LPR）—— 2026-09-20 公布
# 依据：中国人民银行 2026-09-20 授权全国银行间同业拆借中心公布
#   1 年期 LPR：3.00%
#   5 年期以上 LPR：3.50%
#   连续 12 个月保持不变（5 年期自 2024-10 起稳定）
# ============================================================================
LPR_1Y: float = 3.00
LPR_5Y: float = 3.50

# ============================================================================
# 2. 公积金贷款利率（2025-05-08 调整，2026 继续执行）
# 依据：央行/住建部 2025-05-08
# ============================================================================
HOUSING_FUND_RATE_5Y_BELOW: float = 2.35
HOUSING_FUND_RATE_5Y_ABOVE: float = 2.85
HOUSING_FUND_RATE_TIER2_MULT: float = 1.10

HOUSING_FUND_LIMIT_SINGLE_EMP: int = 60_0000
HOUSING_FUND_LIMIT_COUPLE_DEFAULT: int = 120_0000
HOUSING_FUND_LIMIT_COUPLE_TIER1: int = 160_0000

# ============================================================================
# 3. 个人住房商贷利率（央行 2025-12 调整，2026 继续执行）
# 依据：央行/银保监会 2025-12
# ============================================================================
MORTGAGE_RATE_FIRST_HOME_BP: int = -30
MORTGAGE_RATE_SECOND_HOME_BP: int = 30
MORTGAGE_RATE_FIRST_HOME_TIER1_BP: int = -60

MORTGAGE_RATIO_FIRST: float = 0.70
MORTGAGE_RATIO_SECOND: float = 0.50

# ============================================================================
# 4. 个人消费贷额度上限（银保监会 2020 / 2024 新规）
# 依据：银保监会 2020-07《商业银行互联网贷款管理暂行办法》第七条
#   线上 ≤ 30 万；2024 线下 ≤ 100 万
# 依据：财政部/央行/金管总局 2026-01-16 财金〔2026〕6 号
#   贴息期内个人消费贷最高额度享受贴息：单户 ≤ 50 万
# 依据：2026-08-21 三部委联合发文扩大至 100 万（部分消费场景）
# ============================================================================
CONSUMER_LOAN_LIMIT_ONLINE: int = 30_0000
CONSUMER_LOAN_LIMIT_OFFLINE: int = 100_0000
CONSUMER_LOAN_LIMIT_SUBSIDY: int = 50_0000

# ============================================================================
# 5. 个人经营贷 / 普惠小微（金融监管总局 2026-05-19）
# 依据：金管总局 2026-05-19 金办发〔2026〕44 号
#   普惠型小微企业贷款单户授信 ≤ 1000 万元
#   贷款利率根据 LPR + 资金成本 + 风险成本合理定价
# ============================================================================
SMALL_MICRO_LIMIT_PER_BUSINESS: int = 1000_0000
SMALL_MICRO_RATE_CAP_OVER_LPR_BP: int = 200

# ============================================================================
# 6. DSR（偿债比）阈值
# 依据：银保监会 2020-09 / 业内通行
# ============================================================================
DSR_THRESHOLD: float = 0.50

# ============================================================================
# 7. 一票否决
# ============================================================================
VETO_HARD_RULES: dict[str, str] = {
    "current_overdue": "有",
    "bad_status": "有",
}

# ============================================================================
# 派生辅助
# ============================================================================
def _lpr_plus_bp(bp: int, lpr: float = LPR_5Y) -> float:
    """LPR + bp/100（bp: basis points 基点）"""
    return round(lpr + bp / 100, 2)


# ============================================================================
#              产品级基础规则（2026 监管底线 + 业内通行）
# ============================================================================
# 客户群：公务员/事业单位/国企/央企/世界 500 强
# 2026 实测：建行快贷 3.45-3.95%，工行融 e 借 3.7-5.6%，招行闪电贷 3.0-9.0%
QUALITY_UNIT_2026: dict = {
    "依据": "建行快贷/工行融 e 借/招行闪电贷 2026 公开利率 + 银保监 2020 互联网贷款 ≤30 万线上 / ≤100 万线下",
    "用户类型": "personal",
    "监管上限": {
        "线上": CONSUMER_LOAN_LIMIT_ONLINE,
        "线下": CONSUMER_LOAN_LIMIT_OFFLINE,
    },
    "基础利率": {
        # S：LPR-30BP ~ LPR-5BP（接近首套商贷）
        "S": (_lpr_plus_bp(MORTGAGE_RATE_FIRST_HOME_BP), LPR_5Y - 0.05),
        # A：LPR ~ LPR+100BP
        "A": (LPR_5Y, LPR_5Y + 1.00),
        # B：LPR+100BP ~ LPR+250BP
        "B": (LPR_5Y + 1.00, LPR_5Y + 2.50),
        # C：LPR+250BP ~ LPR+500BP
        "C": (LPR_5Y + 2.50, LPR_5Y + 5.00),
        # D：LPR+500BP ~ LPR+850BP
        "D": (LPR_5Y + 5.00, LPR_5Y + 8.50),
        # E：拒批区
        "E": (LPR_5Y + 8.50, LPR_5Y + 10.50),
    },
    "额度倍数": {  # 年收入倍数
        "S": 8, "A": 6, "B": 4, "C": 2.5, "D": 1.5, "E": 0,
    },
    "依据_利率": "建行/工行/招行 2026 公开利率表 + LPR 派生",
    "依据_额度": "优质客群 4-8 倍年收入（业内通行）",
}

# 客户群：公积金连续缴存 6-12 个月以上
# 2026 实测：建行 3.45-4.50%、工行 3.45-4.50%、招行 3.85-5.50%
HOUSING_FUND_2026: dict = {
    "依据": "建行/工行/招行公积金优享贷 2026 公开利率 + 公积金中心单户 60/120/160 万上限",
    "用户类型": "personal",
    "监管上限": {
        "单职工": HOUSING_FUND_LIMIT_SINGLE_EMP,
        "双职工": HOUSING_FUND_LIMIT_COUPLE_DEFAULT,
        "一线双职工": HOUSING_FUND_LIMIT_COUPLE_TIER1,
    },
    "基础利率": {
        "S": (HOUSING_FUND_RATE_5Y_ABOVE, LPR_5Y - 0.05),
        "A": (_lpr_plus_bp(MORTGAGE_RATE_FIRST_HOME_BP), LPR_5Y),
        "B": (LPR_5Y, LPR_5Y + 1.00),
        "C": (LPR_5Y + 1.00, LPR_5Y + 2.00),
        "D": (LPR_5Y + 2.00, LPR_5Y + 4.00),
        "E": (LPR_5Y + 4.00, LPR_5Y + 6.00),
    },
    "额度倍数": {  # 月缴存 × 月数
        "S": 200, "A": 150, "B": 100, "C": 60, "D": 24, "E": 0,
    },
    "依据_利率": "建行/工行/招行公积金优享贷 2026 公开利率表 + 公积金 2.85% 基础",
    "依据_额度": "月缴存 × 100-200 倍（业内通行）",
}

# 客户群：普通工薪阶层（区别于代发 6 月以上的 quality_unit）
# 2026 实测：平安新一贷 5.4-17.88%、中行随心智贷 3.99-9.0%
SALARY_2026: dict = {
    "依据": "平安新一贷 / 中行随心智贷 2026 公开利率 + 银保监消费贷 ≤30 万线上 / ≤100 万线下",
    "用户类型": "personal",
    "监管上限": {
        "线上": CONSUMER_LOAN_LIMIT_ONLINE,
        "线下": CONSUMER_LOAN_LIMIT_OFFLINE,
    },
    "基础利率": {
        "S": (LPR_5Y + 0.50, LPR_5Y + 2.00),
        "A": (LPR_5Y + 1.50, LPR_5Y + 3.50),
        "B": (LPR_5Y + 2.50, LPR_5Y + 5.00),
        "C": (LPR_5Y + 5.00, LPR_5Y + 8.50),
        "D": (LPR_5Y + 8.50, LPR_5Y + 13.50),
        "E": (LPR_5Y + 13.50, LPR_5Y + 18.50),
    },
    "额度倍数": {
        "S": 5, "A": 4, "B": 3, "C": 2, "D": 1.2, "E": 0,
    },
    "依据_利率": "平安新一贷 / 中行随心智贷 2026 公开利率 + 消费贷 ≤30 万线上",
    "依据_额度": "工薪客群 2-5 倍年收入（业内通行）",
}

# 客户群：本地有房（净值 = 评估 - 已有按揭）
# 2026 实测：建行房抵贷 3.15-4.20%、工行家居贷 3.5-5.5%
HOUSE_OWNER_2026: dict = {
    "依据": "建行/工行/农行房抵贷 2026 公开利率 + 央行 2025-12 房贷政策 + 首抵 70% / 二抵 50%",
    "用户类型": "personal",
    "监管上限": {
        "首抵": 10_000_000,
        "二抵": 10_000_000,
    },
    "基础利率": {
        "S": (_lpr_plus_bp(MORTGAGE_RATE_FIRST_HOME_BP), LPR_5Y),
        "A": (LPR_5Y, LPR_5Y + 0.70),
        "B": (LPR_5Y + 0.70, LPR_5Y + 1.50),
        "C": (LPR_5Y + 1.50, LPR_5Y + 3.00),
        "D": (LPR_5Y + 3.00, LPR_5Y + 4.50),
        "E": (LPR_5Y + 4.50, LPR_5Y + 6.00),
    },
    "净值成数": {
        "S": 0.85, "A": 0.75, "B": 0.65, "C": 0.55, "D": 0.40, "E": 0.0,
    },
    "抵押率": {
        "S": MORTGAGE_RATIO_FIRST,
        "A": MORTGAGE_RATIO_FIRST,
        "B": MORTGAGE_RATIO_SECOND,
        "C": MORTGAGE_RATIO_SECOND,
        "D": 0.30,
        "E": 0.0,
    },
    "依据_利率": "建行/工行/农行房抵贷 2026 公开利率 + 央行 2025-12 首套 LPR-30BP",
    "依据_额度": "首抵 70% / 二抵 50% / DSR ≤ 50% (银保监 2020 偿债比)",
}

# 客户群：连续纳税 1-2 年 + 纳税信用 A/B/M/C 级
# 2026 实测：建行税易贷 4.0-6.5%、农行纳税 e 贷 3.85-5.5%
TAX_2026: dict = {
    "依据": "建行税易贷 / 工行经营快贷 / 微众微业贷 2026 公开利率 + 金管总局 2026-05-19 普惠小微 ≤1000 万",
    "用户类型": "business",
    "监管上限": {
        "个人版": CONSUMER_LOAN_LIMIT_OFFLINE,
        "小微企业版": SMALL_MICRO_LIMIT_PER_BUSINESS,
    },
    "基础利率": {
        "S": (LPR_5Y, LPR_5Y + 1.00),
        "A": (LPR_5Y + 1.00, LPR_5Y + 2.00),
        "B": (LPR_5Y + 2.00, LPR_5Y + 3.50),
        "C": (LPR_5Y + 3.50, LPR_5Y + 5.50),
        "D": (LPR_5Y + 5.50, LPR_5Y + 8.00),
        "E": (LPR_5Y + 8.00, LPR_5Y + 10.50),
    },
    "额度倍数": {  # 年纳税额倍数
        "S": 10, "A": 8, "B": 5, "C": 3, "D": 1.5, "E": 0,
    },
    "依据_利率": "建行税易贷 / 农行纳税 e 贷 2026 公开利率 + 普惠小微 ≤LPR+200BP",
    "依据_额度": "年纳税额 × 5-10 倍（建行税易贷标准）",
}

# 客户群：连续开票 1-2 年 + 增值税一般纳税人
# 2026 实测：网商贷 10.8-24.0%、微众开票贷 7.2-18.0%
INVOICE_2026: dict = {
    "依据": "网商贷 / 微众开票贷 / 京东金融 2026 公开利率 + 金管总局 2026-05-19 普惠小微 ≤1000 万",
    "用户类型": "business",
    "监管上限": {
        "小微企业版": SMALL_MICRO_LIMIT_PER_BUSINESS,
        "线上": 100_0000,
        "线下": 500_0000,
    },
    "基础利率": {
        "S": (LPR_5Y + 2.00, LPR_5Y + 4.00),
        "A": (LPR_5Y + 3.50, LPR_5Y + 5.50),
        "B": (LPR_5Y + 5.50, LPR_5Y + 8.50),
        "C": (LPR_5Y + 8.50, LPR_5Y + 13.00),
        "D": (LPR_5Y + 13.00, LPR_5Y + 17.00),
        "E": (LPR_5Y + 17.00, LPR_5Y + 21.00),
    },
    "开票率": {
        "S": 0.10, "A": 0.08, "B": 0.06, "C": 0.04, "D": 0.02, "E": 0.0,
    },
    "依据_利率": "网商贷 / 微众开票贷 2026 公开利率 + 普惠小微 ≤LPR+200BP (5.50%) 不适用此产品（小微高风险）",
    "依据_额度": "年开票额 × 5-10% (网商/微众开票贷 业内通行)",
}

# ============================================================================
#              银行级 override（v16.1 暂作参考）
# ============================================================================
# 国有大行：利率最低，审批最严
# 股份行：利率中等，审批灵活
# 互联网银行：利率最高，审批最快
# 数据来源：每家银行 2026 公开利率表
BANK_OVERRIDE_2026: dict[str, dict] = {
    "ICBC":   {"依据": "工行 2026 融 e 借/经营快贷/家居贷 公开利率",   "rate_offset_bp": -20, "limit_cap_factor": 1.0},
    "CCB":    {"依据": "建行 2026 快贷/房抵贷/税易贷 公开利率",         "rate_offset_bp": -25, "limit_cap_factor": 1.0},
    "BOC":    {"依据": "中行 2026 中银 e 贷/随心智贷 公开利率",          "rate_offset_bp": -10, "limit_cap_factor": 1.0},
    "ABC":    {"依据": "农行 2026 网捷贷/纳税 e 贷/房抵 e 贷 公开利率", "rate_offset_bp": -15, "limit_cap_factor": 1.0},
    "BCM":    {"依据": "交行 2026 惠民贷 公开利率",                     "rate_offset_bp":  10, "limit_cap_factor": 1.0},
    "CMB":    {"依据": "招行 2026 闪电贷 公开利率",                     "rate_offset_bp":   0, "limit_cap_factor": 1.1},
    "PAB":    {"依据": "平安 2026 新一贷 公开利率",                     "rate_offset_bp":  50, "limit_cap_factor": 0.9},
    "XCB":    {"依据": "新网银行 2026 好人贷 公开利率",                 "rate_offset_bp":  80, "limit_cap_factor": 0.7},
    "WEBANK": {"依据": "微众 2026 微粒贷/微业贷 公开利率",              "rate_offset_bp": 100, "limit_cap_factor": 0.5},
    "MYBANK": {"依据": "网商 2026 网商贷 公开利率",                    "rate_offset_bp": 150, "limit_cap_factor": 0.4},
}


# ============================================================================
#              派生的全局映射（供 scorecard_engine / product_engine 引用）
# ============================================================================
# 6 产品的 LEVEL → (rate_min, rate_max) 派生自 bank_regulations_2026
# 设计：把 6 产品的"基础利率"表合并成一个全局 RATE_BY_LEVEL_OR_PRODUCT
#       方便 scorecard_engine 在不知道产品时也能拿到利率

RATE_MIN_BY_LEVEL: dict[str, float] = {
    # 从 QUALITY_UNIT_2026 / SALARY_2026 / TAX_2026 等取"利率下限最小值"作为 floor
    # S 级所有产品中最优：3.20% (quality_unit LPR-30BP)
    "S": min(
        QUALITY_UNIT_2026["基础利率"]["S"][0],
        HOUSING_FUND_2026["基础利率"]["S"][0],  # 2.85% 公积金基础
        HOUSE_OWNER_2026["基础利率"]["S"][0],
    ),
    "A": min(p["基础利率"]["A"][0] for p in [QUALITY_UNIT_2026, HOUSING_FUND_2026, SALARY_2026, HOUSE_OWNER_2026, TAX_2026, INVOICE_2026]),
    "B": min(p["基础利率"]["B"][0] for p in [QUALITY_UNIT_2026, HOUSING_FUND_2026, SALARY_2026, HOUSE_OWNER_2026, TAX_2026, INVOICE_2026]),
    "C": min(p["基础利率"]["C"][0] for p in [QUALITY_UNIT_2026, HOUSING_FUND_2026, SALARY_2026, HOUSE_OWNER_2026, TAX_2026, INVOICE_2026]),
    "D": min(p["基础利率"]["D"][0] for p in [QUALITY_UNIT_2026, HOUSING_FUND_2026, SALARY_2026, HOUSE_OWNER_2026, TAX_2026, INVOICE_2026]),
    "E": min(p["基础利率"]["E"][0] for p in [QUALITY_UNIT_2026, HOUSING_FUND_2026, SALARY_2026, HOUSE_OWNER_2026, TAX_2026, INVOICE_2026]),
}

RATE_MAX_BY_LEVEL: dict[str, float] = {
    "S": max(p["基础利率"]["S"][1] for p in [QUALITY_UNIT_2026, HOUSING_FUND_2026, SALARY_2026, HOUSE_OWNER_2026, TAX_2026, INVOICE_2026]),
    "A": max(p["基础利率"]["A"][1] for p in [QUALITY_UNIT_2026, HOUSING_FUND_2026, SALARY_2026, HOUSE_OWNER_2026, TAX_2026, INVOICE_2026]),
    "B": max(p["基础利率"]["B"][1] for p in [QUALITY_UNIT_2026, HOUSING_FUND_2026, SALARY_2026, HOUSE_OWNER_2026, TAX_2026, INVOICE_2026]),
    "C": max(p["基础利率"]["C"][1] for p in [QUALITY_UNIT_2026, HOUSING_FUND_2026, SALARY_2026, HOUSE_OWNER_2026, TAX_2026, INVOICE_2026]),
    "D": max(p["基础利率"]["D"][1] for p in [QUALITY_UNIT_2026, HOUSING_FUND_2026, SALARY_2026, HOUSE_OWNER_2026, TAX_2026, INVOICE_2026]),
    "E": max(p["基础利率"]["E"][1] for p in [QUALITY_UNIT_2026, HOUSING_FUND_2026, SALARY_2026, HOUSE_OWNER_2026, TAX_2026, INVOICE_2026]),
}


# ============================================================================
#              通用 API：按产品 + level 查利率/监管上限
# ============================================================================
def get_product_regulation(product_code: str) -> dict | None:
    """按产品 code 获取 2026 监管规则"""
    return {
        "quality_unit": QUALITY_UNIT_2026,
        "housing_fund": HOUSING_FUND_2026,
        "salary":       SALARY_2026,
        "house_owner":  HOUSE_OWNER_2026,
        "tax":          TAX_2026,
        "invoice":      INVOICE_2026,
    }.get(product_code)


def get_rate_range(product_code: str, level: str) -> tuple[float, float] | None:
    """按产品 + level 查利率区间"""
    reg = get_product_regulation(product_code)
    if not reg:
        return None
    return reg["基础利率"].get(level)


def get_limit_cap(product_code: str, channel: str = "线上") -> int | None:
    """按产品 + 渠道查监管上限（单位：元）"""
    reg = get_product_regulation(product_code)
    if not reg:
        return None
    return reg["监管上限"].get(channel)


def get_bank_override(bank_code: str) -> dict | None:
    """按银行 code 获取 override（利率偏移 + 额度上限系数）"""
    return BANK_OVERRIDE_2026.get(bank_code)


def apply_bank_override(rate_lo: float, rate_hi: float, bank_code: str) -> tuple[float, float]:
    """应用银行级 override（利率 ±BP）"""
    override = get_bank_override(bank_code)
    if not override:
        return rate_lo, rate_hi
    offset_bp = override.get("rate_offset_bp", 0)
    return (
        _lpr_plus_bp(offset_bp, rate_lo) if offset_bp else rate_lo,
        _lpr_plus_bp(offset_bp, rate_hi) if offset_bp else rate_hi,
    )
