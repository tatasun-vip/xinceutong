"""
银行差异化评分（v7 增量）

核心理念：不同银行的审批侧重点完全不同，必须按银行特征调整评分权重。

设计：
  - BANK_FOCUS：每家银行重点关注的产品类型（优先级排序）
  - BANK_BIAS：每家银行的评分微调（基于 features 关键词匹配）
  - BANK_SLOGAN：前端展示用的"评估侧重点"短句

调用方：
  - product_engine.calculate_scores_by_product 接收 bank_features 参数
  - 对每个产品结果按银行 focus 调整 score
  - assessment.py submit 时把银行 features 传进去

数据来源：
  - banks 表的 features 字段（seed_banks.py 已 seed）
  - 这里是「配置层」（银行 × 产品维度的权重），与 ScorecardRule（数据层）解耦
"""
from __future__ import annotations
from typing import Any


# ============================================================================
# 10 家银行的 focus + 关键标签（与 seed_banks.py features 对齐）
# ============================================================================

BANK_FOCUS: dict[str, dict[str, Any]] = {
    # 国有大行
    "ICBC": {
        "key_products": ["quality_unit", "housing_fund", "salary"],
        "key_tags": ["代发工资优待", "公积金专项", "利率最低", "审批严格"],
        "weight": {"housing_fund": 1.5, "salary": 1.3, "quality_unit": 1.2},
        "veto_soft": True,   # 一票否决较严
    },
    "CCB": {
        "key_products": ["house_owner", "quality_unit"],
        "key_tags": ["房产抵押利率低", "快贷速度快", "客户经理响应快"],
        "weight": {"house_owner": 1.6, "quality_unit": 1.2},
        "veto_soft": True,
    },
    "BOC": {
        "key_products": ["quality_unit", "tax"],
        "key_tags": ["外汇业务强", "外贸企业友好", "海外背景优待"],
        "weight": {"quality_unit": 1.2, "tax": 1.3},
        "veto_soft": False,
    },
    "ABC": {
        "key_products": ["salary", "house_owner"],
        "key_tags": ["下沉市场广", "县域客户优待", "公务员专项"],
        "weight": {"salary": 1.2, "house_owner": 1.2},
        "veto_soft": True,
    },
    "BCOM": {
        "key_products": ["quality_unit", "salary"],
        "key_tags": ["惠民贷口碑好", "审批快", "优质单位友好"],
        "weight": {"quality_unit": 1.4, "salary": 1.2},
        "veto_soft": False,
    },
    # 股份制
    "CMB": {
        "key_products": ["salary", "quality_unit"],
        "key_tags": ["零售之王", "闪电贷 3 分钟", "已有客户额度优"],
        "weight": {"salary": 1.3, "quality_unit": 1.3},
        "veto_soft": False,
    },
    "PAB": {
        "key_products": ["salary", "tax"],
        "key_tags": ["额度上限高", "负债容忍度高", "保险客户优待"],
        "weight": {"salary": 1.3, "tax": 1.2},
        "veto_soft": False,
        "limit_boost": 1.2,  # 额度上限高
    },
    # 互联网银行
    "XCB": {
        "key_products": ["salary", "quality_unit"],
        "key_tags": ["互联网纯线上", "准入门槛低", "审批快"],
        "weight": {"salary": 1.1, "quality_unit": 1.1},
        "veto_soft": False,   # 准入门槛低
        "veto_relax": True,   # 一票否决较松
    },
    "WEBANK": {
        "key_products": ["salary", "quality_unit"],
        "key_tags": ["腾讯系", "扫码即贷", "按日计息", "无抵押"],
        "weight": {"salary": 1.1, "quality_unit": 1.1},
        "veto_soft": False,
        "veto_relax": True,
    },
    "MYBANK": {
        "key_products": ["tax", "invoice"],
        "key_tags": ["阿里系", "小微专属", "电商卖家专项", "流水贷"],
        "weight": {"tax": 1.3, "invoice": 1.4},
        "veto_soft": False,
        "veto_relax": True,
    },
}


# ============================================================================
# 银行 focus 短句（前端 UI 展示用，10~14 字）
# ============================================================================

BANK_FOCUS_SLOGAN: dict[str, str] = {
    "ICBC": "侧重公积金 + 代发工资",
    "CCB": "侧重房产抵押",
    "BOC": "侧重优质单位 + 纳税",
    "ABC": "侧重公务员 + 房产",
    "BCOM": "侧重优质单位",
    "CMB": "侧重工资流水 + 优质单位",
    "PAB": "侧重高额度 + 负债容忍",
    "XCB": "互联网纯线上 · 准入宽松",
    "WEBANK": "腾讯系 · 扫码即贷",
    "MYBANK": "阿里系 · 电商流水贷",
}


# ============================================================================
# 核心函数
# ============================================================================

def get_bank_focus_slogan(bank_code: str | None) -> str:
    """前端展示用的「评估侧重点」短句"""
    if not bank_code:
        return "通用信用模型"
    return BANK_FOCUS_SLOGAN.get(bank_code, "通用信用模型")


def get_bank_weight(bank_code: str | None, product_code: str) -> float:
    """获取某家银行对某产品的评分权重（默认 1.0 = 无调整）"""
    if not bank_code:
        return 1.0
    cfg = BANK_FOCUS.get(bank_code)
    if not cfg:
        return 1.0
    return float(cfg.get("weight", {}).get(product_code, 1.0))


def apply_bank_bias(
    raw_score: float,
    bank_code: str | None,
    product_code: str,
) -> float:
    """
    按银行 focus 对单个产品 raw_score 调整
    （在 [0, 100] 区间内加权，超出 clamp）
    """
    w = get_bank_weight(bank_code, product_code)
    if w == 1.0:
        return raw_score
    biased = raw_score * w
    return max(0.0, min(100.0, biased))


def get_bank_limit_boost(bank_code: str | None) -> float:
    """某些银行额度上限更高（如 PAB 50 万），前端的额度封顶可微调"""
    if not bank_code:
        return 1.0
    cfg = BANK_FOCUS.get(bank_code)
    if not cfg:
        return 1.0
    return float(cfg.get("limit_boost", 1.0))


def is_veto_relax(bank_code: str | None) -> bool:
    """互联网银行对硬查询/逾期的容忍度更高（XCB / WEBANK / MYBANK）"""
    if not bank_code:
        return False
    cfg = BANK_FOCUS.get(bank_code)
    return bool(cfg and cfg.get("veto_relax", False))


def get_bank_key_tags(bank_code: str | None) -> list[str]:
    """前端 UI 展示的银行 3~4 个特点标签"""
    if not bank_code:
        return []
    cfg = BANK_FOCUS.get(bank_code)
    return list(cfg.get("key_tags", [])) if cfg else []
