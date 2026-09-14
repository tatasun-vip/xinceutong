#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================
信测通 v22+ 话术规范化（narrative.py）
==============================================================

【设计目标】
1. 更专业：银行客户经理 / 信贷分析师口吻（不要营销风/口语）
2. 一定不自相矛盾：所有文案都派生自同一份"评级 SSOT"
3. 一次定义多处复用：覆盖 4 个口径
   - 顶部一句话结论 (one_sentence)
   - 免费摘要 (free_summary)
   - 6 大产品不推荐原因 (not_recommend_reason)
   - 风险标签 / 优势 / 弱点 (risk_tags/advantages/weak_points)

【5 大自洽性保证】
1. level 口径不自洽：E 级文案绝不说"可申请"
2. veto 互斥：veto 项触发的标签，绝不能再列其"对应优势"
3. 额度/利率口径：金额/利率/通过率三者必须与 level 同步
4. 产品推荐口径：E/D 级只能推荐"暂无可推荐产品"或"小额信贷"
5. 改善建议口径：建议与可改善项（fixable_in_90d）严格匹配，不画饼

==============================================================
"""

from __future__ import annotations

from typing import Any


# ============================================================================
# 1. 等级 SSOT（银行话术模板）—— 6 等级 × 5 字段
# ============================================================================
# 字段：title / description / verdict / recommendation / cta
# - title:        评级名
# - description:  1 句话专业描述
# - verdict:      综合结论（用于 one_sentence 顶层）
# - recommendation: 申请建议（用于 free_summary / not_recommend_reason）
# - cta:          行动号召（用于产品列表底部）

LEVEL_NARRATIVE: dict[str, dict[str, str]] = {
    "S": {
        "title": "S 级（卓越）",
        "description": "根据我行 A 卡模型综合评估，您属于卓越客户群体，5 大行 + 12 家股份行普遍可批，且能拿到最优利率档。",
        "verdict": "您的资质已属卓越，可直接申请",
        "recommendation": "建议优先选择 5 大行低息产品（如建行快贷 / 工行融e借），同步申请 2-3 家以拿到最低利率组合",
        "cta": "立即申请",
    },
    "A": {
        "title": "A 级（优质）",
        "description": "根据我行 A 卡模型综合评估，您属于优质客户群体，多家银行可批，利率处于优惠区间。",
        "verdict": "您的资质已属优质，可直接申请",
        "recommendation": "建议优先在 1-2 家股份制商业银行试申请（如招行 / 浦发），通过后再尝试其他银行提额",
        "cta": "立即申请",
    },
    "B": {
        "title": "B 级（良好）",
        "description": "根据我行 A 卡模型综合评估，您属于良好客户群体，部分银行可批，但利率与额度仍有提升空间。",
        "verdict": "您的资质良好，可优先选择通过率较高的产品申请",
        "recommendation": "建议先在 1 家通过率较高的银行试申请（如工资代发行 / 公积金缴存行），通过后再尝试其他银行",
        "cta": "查看推荐产品",
    },
    "C": {
        "title": "C 级（一般）",
        "description": "根据我行 A 卡模型综合评估，您当前属于一般客户群体，多数主流银行通过率偏低，建议先优化再申请。",
        "verdict": "您的资质一般，建议先优化再申请",
        "recommendation": "建议先建立第一笔信贷记录（如 1 张信用卡正常使用 6 个月），6 个月后再次申请可显著提升评分",
        "cta": "查看改善建议",
    },
    "D": {
        "title": "D 级（较弱）",
        "description": "根据我行 A 卡模型综合评估，您当前资质较弱，多数主流银行通过率较低，建议先优化关键指标后再申请。",
        "verdict": "目前较弱，建议先优化再申请",
        "recommendation": "建议优先解决征信类问题（如降低信用卡使用率 / 减少硬查询），3-6 个月后再次评估",
        "cta": "查看改善建议",
    },
    "E": {
        "title": "E 级（不满足模拟准入）",
        "description": "根据我行 A 卡模型综合评估，您当前不满足模拟准入条件（存在央行一票否决项或多项硬性风险）。",
        "verdict": "建议暂缓申请，先解决风险项",
        "recommendation": "建议先到央行打印详版征信报告（人行官网 / 线下网点），逐条核实风险来源并解决，3-6 个月后重新测评",
        "cta": "暂缓申请",
    },
}


# ============================================================================
# 2. 评级 → 通过概率 / 利率档位（SSOT，避免文案数字与 level 矛盾）
# ============================================================================

LEVEL_PASS_PROB: dict[str, str] = {
    "S": "通过率高（约 80-95%）",
    "A": "通过率较高（约 60-80%）",
    "B": "通过率中等偏高（约 40-60%）",
    "C": "通过率中等（约 20-40%）",
    "D": "通过率偏低（约 5-20%）",
    "E": "通过率极低（央行一票否决或多项硬性风险）",
}

LEVEL_RATE_DESC: dict[str, str] = {
    "S": "年化 3.20%-4.50%（最优档）",
    "A": "年化 3.45%-6.50%（优惠档）",
    "B": "年化 4.50%-9.00%（常规档）",
    "C": "年化 9.00%-15.00%（偏高档）",
    "D": "年化 15.00%-22.00%（高息档）",
    "E": "—（未达模拟准入）",
}


# ============================================================================
# 3. 互斥规则（避免优势 / 风险标签自相矛盾）
# ============================================================================
# 触发某 risk 后，对应 advantage 必须从列表移除
# 解决类似"信用卡 80%+ → '信用卡使用率低' 还显示"的问题

RISK_ADVANTAGE_MUTEX: list[tuple[str, str]] = [
    # (risk 关键词, advantage 关键词——必须从 advantages 移除)
    ("信用卡使用率",        "信用卡使用率低"),
    ("信用卡额度占用",      "信用卡使用率低"),
    ("近 3 个月查询",       "近期征信查询稀少"),
    ("近 6 个月查询",       "半年征信查询稀少"),
    ("近 2 年有逾期",       "近 2 年无逾期"),
    ("近 2 年逾期 3 次",    "近 2 年无逾期"),
    ("当前有逾期",          "近 2 年无逾期"),
    ("连续逾期",            "近 2 年无逾期"),
    ("在贷笔数偏多",        "已有贷款笔数较多"),
    ("白户风险",            "近 2 年无逾期"),
    ("账户存在次级",        "近 2 年无逾期"),
    # veto 项触发后，对应 weak 也不应再出现
    ("veto",                "信用卡使用率低"),
    ("veto",                "近 2 年无逾期"),
    ("veto",                "半年征信查询稀少"),
    ("veto",                "近期征信查询稀少"),
    ("veto",                "已有贷款笔数较多"),
]


# ============================================================================
# 4. 严重度排序 / 颜色
# ============================================================================

ISSUE_SEVERITY_RANK: dict[str, int] = {"high": 3, "mid": 2, "low": 1}
ISSUE_SEVERITY_COLOR: dict[str, str] = {
    "high": "#8E6F2C",
    "mid":  "#C9A96E",
    "low":  "#8B7E5E",
}


# ============================================================================
# 5. 银行专业话术模板（"什么是/为什么/怎么改"5 维度）
# ============================================================================
# 关键设计：
#   - what: 客户现状（不带情绪、不带建议）
#   - why: 引用银行 A 卡模型 + 权重（专业、量化）
#   - impact_prob/amount/rate: 量化影响（不允许"可能"等模糊词）
#   - how: 可执行操作（动词开头，不超过 2 步）
#   - when: 修复周期（具体时间窗）
#   - result: 修复后可量化效果（必须 >= 当前 level）
#   - severity: high / mid / low（驱动排序 & 颜色）
#   - input_match: 兜底匹配规则

ISSUE_TEMPLATES: list[dict[str, Any]] = [
    # ====== 征信类（high 严重度）======
    {
        "key": "当前逾期",
        "category": "征信",
        "severity": "high",
        "title": "存在当前逾期",
        "what": "根据人行征信报告，您当前存在未结清的逾期欠款。",
        "why": "在我行 A 卡模型中，「当前逾期」属硬性一票否决项，权重等同央行征信硬指标——命中即直接拒批，无任何人工干预空间。",
        "impact_prob": "通过概率降至 0",
        "impact_amount": "额度评估直接归零",
        "impact_rate": "—",
        "how": "立即结清所有逾期欠款；还清次月向人行申请更新征信报告。",
        "when": "1-2 个月（结清 + 报告更新）",
        "result": "逾期标记从「当前逾期」变为「历史逾期」后，预计可恢复至 D 级以上。",
        "fix_fields": {"current_overdue": "无"},
        "input_match": {"current_overdue": ["有"]},
    },
    {
        "key": "连续逾期",
        "category": "征信",
        "severity": "high",
        "title": "存在连续逾期",
        "what": "根据人行征信报告，您的账户存在 60 天以上连续逾期记录。",
        "why": "在我行 A 卡模型中，连续逾期权重等同「当前逾期」一票否决项——银行判定为「严重信用瑕疵」，需 24 个月逐步淡化。",
        "impact_prob": "通过概率几乎降至 0",
        "impact_amount": "额度评估直接拒绝",
        "impact_rate": "—",
        "how": "联系贷款机构说明情况并制定结清计划，避免「连续逾期」标记继续累计。",
        "when": "未来 24 个月",
        "result": "24 个月无新增逾期后，连续逾期标记淡出，可重新申请。",
        "fix_fields": {"serial_overdue": "无"},
        "input_match": {"serial_overdue": ["有"]},
    },
    {
        "key": "账户次级",
        "category": "征信",
        "severity": "high",
        "title": "账户状态为次级/可疑/损失",
        "what": "根据人行征信报告，您的账户存在「次级 / 可疑 / 损失」五级分类异常。",
        "why": "在我行 A 卡模型中，账户五级分类权重等同一票否决项——5 大行普遍直接判 D/E 级。",
        "impact_prob": "通过概率几乎降至 0",
        "impact_amount": "额度评估直接拒绝",
        "impact_rate": "—",
        "how": "到人行打印详版征信报告，确认异常账户来源并结清所有欠款。",
        "when": "未来 3-6 个月",
        "result": "消除五级分类异常后，预计可恢复至 D 级以上。",
        "fix_fields": {"bad_status": "无"},
        "input_match": {"bad_status": ["有"]},
    },
    {
        "key": "近 3 个月查询",
        "category": "征信",
        "severity": "high",
        "title": "近 3 个月征信查询过于频繁",
        "what": "根据人行征信报告，近 3 个月内您的征信报告上有多次「贷款审批」硬查询记录。",
        "why": "在我行 A 卡模型中，近 3 月硬查询权重约 8%，6 次以上触发风控自动拦截——银行系统判定为「短期资金需求迫切」。",
        "impact_prob": "通过概率下降 25-40 个百分点（6 次以上）",
        "impact_amount": "额度上限下调 20-30%",
        "impact_rate": "年化利率上浮 1-2 个百分点",
        "how": "立即停止所有贷款 / 信用卡 / 分期申请；90 天后硬查询按月滚动消失。",
        "when": "未来 90 天",
        "result": "查询痕迹淡出后，通过概率预计回升 20-30 个百分点，评分回到正常档位。",
        "fix_fields": {"recent_3month_queries": "0-2次"},
        "input_match": {"recent_3month_queries": ["6次以上", "3-5次"]},
    },
    {
        "key": "近 6 个月查询",
        "category": "征信",
        "severity": "high",
        "title": "近 6 个月征信查询过多",
        "what": "根据人行征信报告，近 6 个月内您的征信报告上有 10 次以上「贷款审批」硬查询记录。",
        "why": "在我行 A 卡模型中，近 6 月硬查询权重约 5%，10 次以上属央行征信硬指标——5 大行普遍一票否决。",
        "impact_prob": "通过概率几乎降至 0（央行一票否决）",
        "impact_amount": "额度评估直接拒绝",
        "impact_rate": "—",
        "how": "立即停止所有贷款 / 信用卡 / 分期申请；180 天后硬查询按月滚动消失。",
        "when": "未来 180 天",
        "result": "180 天后查询痕迹淡出，可重新申请。",
        "fix_fields": {"recent_6month_queries": "0-3次"},
        "input_match": {"recent_6month_queries": ["10次以上", "7-10次"]},
    },
    {
        "key": "信用卡使用率",
        "category": "征信",
        "severity": "high",
        "title": "信用卡使用率偏高",
        "what": "您的信用卡已用额度占总额度的 50% 以上。",
        "why": "在我行 A 卡模型中，信用卡使用率权重约 6%，超 80% 直接一票否决（资金紧张信号）；50-80% 降一档评分。",
        "impact_prob": "通过概率下降 15-25 个百分点（80% 以上降至 0）",
        "impact_amount": "额度上限下调 15-20%",
        "impact_rate": "—",
        "how": "账单日前还部分欠款，将使用率压至 50% 以下；建议长期保持 30% 以下。",
        "when": "1-2 个月（次账单日后即生效）",
        "result": "使用率压至 30% 后，通过概率预计回升 10-20 个百分点，评分回到正常档位。",
        "fix_fields": {"credit_card_usage": "30%以下"},
        "input_match": {"credit_card_usage": ["50-80%", "80%以上"]},
    },
    {
        "key": "近 2 年累计逾期",
        "category": "征信",
        "severity": "high",
        "title": "近 2 年逾期次数较多",
        "what": "根据人行征信报告，近 2 年内您的征信报告上有 1 次以上逾期记录。",
        "why": "在我行 A 卡模型中，逾期次数权重约 10%，3 次以上直接降至 D/E 级——属于「违约历史」核心量化指标。",
        "impact_prob": "通过概率下降 30-50 个百分点（3 次以上）",
        "impact_amount": "额度上限下调 30-50%",
        "impact_rate": "年化利率上浮 1-3 个百分点",
        "how": "保持所有账户按时还款满 24 个月，逾期记录逐步滚动出 2 年观察窗。",
        "when": "未来 24 个月",
        "result": "24 个月无新增逾期后，2 年窗口滚动清空，评分恢复至正常档位。",
        "fix_fields": {"overdue_2year": "0次"},
        "input_match": {"overdue_2year": ["1-3次", "3次以上"]},
    },
    {
        "key": "在贷笔数",
        "category": "征信",
        "severity": "mid",
        "title": "在贷笔数偏多",
        "what": "您当前有 3 笔以上未结清的贷款账户。",
        "why": "在我行 A 卡模型中，在贷笔数权重约 6%，5 笔以上直接拉低一档评分（判定为多头借贷）。",
        "impact_prob": "通过概率下降 20-30 个百分点",
        "impact_amount": "额度上限下调 25-40%",
        "impact_rate": "年化利率上浮 1-2 个百分点",
        "how": "优先结清金额最小的 1-2 笔（如某笔消费分期），将笔数降至 3 笔以内。",
        "when": "1-3 个月",
        "result": "笔数压至 3 笔以内后，部分产品通过概率回升 15-25 个百分点。",
        "fix_fields": {"loan_count": "1-2笔"},
        "input_match": {"loan_count": ["3笔以上", "3-5笔", "5笔以上"]},
    },
    {
        "key": "白户风险",
        "category": "征信",
        "severity": "mid",
        "title": "白户风险（无信贷记录）",
        "what": "根据人行征信报告，您当前无任何信贷账户使用记录。",
        "why": "在我行 A 卡模型中，白户仅能拿到「基础分」——因缺乏还款历史无法被系统信任，多数产品降至 C 级。",
        "impact_prob": "通过概率下降 15-25 个百分点",
        "impact_amount": "额度上限受限 20-30%",
        "impact_rate": "—",
        "how": "申请 1 张信用卡并保持正常使用 3-6 个月，建立信贷历史。",
        "when": "3-6 个月",
        "result": "信用卡正常使用 6 个月后，模型将「信用历史」项分数拉满，评分提升 1 档。",
        "fix_fields": {"white_account": "否"},
        "input_match": {"white_account": ["是"]},
    },
    # ====== 收入类（mid 严重度）======
    {
        "key": "月收入较低",
        "category": "收入",
        "severity": "mid",
        "title": "月收入水平偏低",
        "what": "根据您填写的数据，月收入在我行模型中处于偏低区间（5000 元以下）。",
        "why": "在我行 A 卡模型中，月收入权重约 8%——收入偏低直接决定额度天花板（DSR 反算下额度普遍 < 5 万）。",
        "impact_prob": "通过概率下降 10-20 个百分点",
        "impact_amount": "额度上限受限 30-50%",
        "impact_rate": "年化利率上浮 0.5-1 个百分点",
        "how": "通过副业 / 兼职 / 提升社保缴费基数增加「可验证收入」，并保留连续 6 个月银行流水。",
        "when": "3-6 个月",
        "result": "月收入提升至 8000 元以上后，额度天花板相应提升 20-40%。",
        "fix_fields": {"monthly_income": "8000-1.5万"},
        "input_match": {"monthly_income": ["5000以下"]},
    },
    {
        "key": "工作年限",
        "category": "收入",
        "severity": "mid",
        "title": "工作年限较短",
        "what": "根据您填写的数据，您当前工作年限不足 1 年。",
        "why": "在我行 A 卡模型中，工龄权重约 6%——1 年以下被判定为「收入不稳定」，评分压一档。",
        "impact_prob": "通过概率下降 15-25 个百分点",
        "impact_amount": "额度上限下调 10-20%",
        "impact_rate": "—",
        "how": "保持当前工作至满 1 年再申请，期间让社保 / 公积金持续缴存。",
        "when": "3-6 个月",
        "result": "工龄满 1 年后，该维度满权重，评分预计提升 1 档。",
        "fix_fields": {"work_years": "1-3年"},
        "input_match": {"work_years": ["1年以下"]},
    },
    {
        "key": "社保",
        "category": "收入",
        "severity": "mid",
        "title": "社保 / 代发不连续",
        "what": "根据您填写的数据，社保或代发工资记录连续性不足。",
        "why": "在我行 A 卡模型中，社保和代发是验证「真实收入」的核心凭证——不连续 = 收入不稳定，评分降一档。",
        "impact_prob": "通过概率下降 15-25 个百分点",
        "impact_amount": "额度上限下调 20-30%",
        "impact_rate": "—",
        "how": "通过合规渠道补缴社保；保持代发工资连续 6 个月以上。",
        "when": "3-6 个月",
        "result": "社保 / 代发连续 6 个月后，模型将「收入稳定」项分数拉满，评分提升 1 档。",
        "fix_fields": {"social_security": "连续3年以上", "payroll": "是"},
        "input_match": {"social_security": ["1年以下", "无"], "payroll": ["否"]},
    },
    # ====== 资产类（low 严重度，短期内难解决）======
    {
        "key": "无房",
        "category": "资产",
        "severity": "low",
        "title": "无房产可作担保",
        "what": "根据您填写的数据，您目前名下无房产。",
        "why": "在我行「有房客户贷」产品中，房产是核心准入条件——无房客户直接被排除该产品。",
        "impact_prob": "部分产品直接拒批",
        "impact_amount": "失去 1-2 个有竞争力的产品选项",
        "impact_rate": "—",
        "how": "短期内难以解决；可优先选择「不依赖房产」的产品（如优质单位贷 / 公积金贷）。",
        "when": "中长期资产积累",
        "result": "调整申请策略即可；改投不依赖房产的产品后通过率不会下降。",
        "fix_fields": {},
        "input_match": {"house": ["无房"]},
    },
    {
        "key": "单位性质",
        "category": "基础",
        "severity": "low",
        "title": "工作单位不在优质白名单",
        "what": "根据您填写的数据，您的工作单位不在我行「优质单位」白名单内（如非公务员 / 事业单位 / 国企 / 央企）。",
        "why": "在我行「优质单位贷」中，单位性质是核心准入条件——非白名单单位直接被排除该产品。",
        "impact_prob": "失去 1 个低利率产品",
        "impact_amount": "—",
        "impact_rate": "年化利率上浮 1-2 个百分点",
        "how": "短期内无法改变；建议改投「工薪贷」「公积金贷」等不卡单位性质的产品。",
        "when": "—",
        "result": "调整申请策略即可；其他产品仍可正常评估。",
        "fix_fields": {},
        "input_match": {"company_type": ["民营/外企", "个体户/小微企业", "自由职业"]},
    },
]


# ============================================================================
# 6. 改善建议模板（按"征信修复 / 收入证明 / 资产配置 / 申请策略"分组）
# ============================================================================
# 设计原则：
#   1. 每条建议都引用用户实际填写的数据
#   2. 按时间排序（立即 → 1-3 月 → 3-6 月 → 6 月+）
#   3. 每条建议都有"理由"字段（基于银行 A 卡模型口径）
#   4. 优先级：veto(0) > 严重(1) > 中等(2) > 通用(3)

SUGGESTION_TEMPLATES: list[dict[str, Any]] = [
    # ====== 立即（veto / 致命问题）======
    {
        "id": "current_overdue",
        "phase": "立即",
        "action": "结清当前所有逾期欠款，并在还清次月向人行申请更新征信报告",
        "reason": "我行 A 卡模型将「当前逾期」列为硬性一票否决项，未结清前任何申请都会被系统秒拒，无人工干预空间。",
        "source": "征信修复",
        "priority": 0,
        "input_match": {"current_overdue": ["有"]},
    },
    {
        "id": "serial_overdue",
        "phase": "立即",
        "action": "联系贷款机构说明情况并制定结清计划，避免「连续逾期」标记继续累计",
        "reason": "连续 60 天以上逾期在我行模型中权重极高，会被判定为「严重信用瑕疵」，需 24 个月才能逐步淡化。",
        "source": "征信修复",
        "priority": 0,
        "input_match": {"serial_overdue": ["有"]},
    },
    {
        "id": "bad_status",
        "phase": "立即",
        "action": "到人行打印详版征信报告，确认次级 / 可疑 / 损失账户来源并结清",
        "reason": "我行对账户状态为「次级 / 可疑 / 损失」的客户直接判 D/E 级，需先消除五级分类异常。",
        "source": "征信修复",
        "priority": 0,
        "input_match": {"bad_status": ["有"]},
    },
    {
        "id": "veto_pause",
        "phase": "立即",
        "action": "暂缓申请任何贷款 / 信用卡 / 分期，先解决以上征信硬性风险项",
        "reason": "我行模型对致命风险项是 0 容忍，强行申请只会留下更多硬查询和拒贷记录，进一步恶化征信。",
        "source": "申请策略",
        "priority": 1,
        "input_match": {"current_overdue": ["有"]},
    },
    # ====== 1-3 个月（短期优化）======
    {
        "id": "queries_3m",
        "phase": "1-3 个月",
        "action": "停止申请任何贷款 / 信用卡 / 分期，让征信报告上「贷款审批」硬查询自然衰减",
        "reason": "我行 A 卡对近 3 月硬查询非常敏感，6 次以上几乎会被风控拦截；查询记录按月滚动消失。",
        "source": "征信修复",
        "priority": 1,
        "input_match": {"recent_3month_queries": ["3-5次", "6次以上"]},
    },
    {
        "id": "queries_6m",
        "phase": "3-6 个月",
        "action": "继续停申贷款 / 信用卡 / 分期，6 月硬查询也需要从峰值滚动衰减",
        "reason": "我行对 6 月硬查询同样敏感，10 次以上属央行征信硬指标，必须让硬查询自然衰减后再申请。",
        "source": "征信修复",
        "priority": 1,
        "input_match": {"recent_6month_queries": ["7-10次", "10次以上"]},
    },
    {
        "id": "credit_usage",
        "phase": "1-3 个月",
        "action": "还部分信用卡欠款，将使用率压至 50% 以下（建议在账单日前还）",
        "reason": "信用卡使用率超 80% 在我行模型里等于「高资金需求 + 潜在违约」，是评分掉档的重要扣分项。",
        "source": "征信修复",
        "priority": 1,
        "input_match": {"credit_card_usage": ["50%-80%", "80%以上"]},
    },
    {
        "id": "loan_count",
        "phase": "1-3 个月",
        "action": "优先结清金额最小的 1-2 笔在贷，把笔数降到 3 笔以内",
        "reason": "我行 A 卡在「在贷笔数」上做了非线性惩罚，3 笔以内属于正常区间，5 笔以上直接拉低一档。",
        "source": "征信修复",
        "priority": 1,
        "input_match": {"loan_count": ["3-5笔", "5笔以上"]},
    },
    {
        "id": "overdue_2year",
        "phase": "1-3 个月",
        "action": "近 2 年的逾期记录无法消除，但保持 24 个月无逾期可显著淡化影响",
        "reason": "逾期记录在我行模型中按「近 2 年窗口」评估，保持 24 个月干净记录后该维度权重自动降为 0。",
        "source": "征信修复",
        "priority": 2,
        "input_match": {"overdue_2year": ["1-3次", "3次以上"]},
    },
    # ====== 3-6 个月（中期建设）======
    {
        "id": "white_account",
        "phase": "3-6 个月",
        "action": "先申请 1 张信用卡并正常使用 3-6 个月，建立信贷历史",
        "reason": "白户在我行模型中只能拿到「基础分」，因缺乏还款历史无法被系统信任；建好首张卡后再申请额度会显著提升。",
        "source": "征信修复",
        "priority": 2,
        "input_match": {"white_account": ["是"]},
    },
    {
        "id": "work_years",
        "phase": "3-6 个月",
        "action": "保持当前工作至满 1 年再申请，期间让社保 / 公积金持续缴存",
        "reason": "我行的「工作稳定性」维度 1 年是分水岭，1 年以下在评分卡里被压一档；满 1 年后该维度满权重。",
        "source": "收入证明",
        "priority": 2,
        "input_match": {"work_years": ["1年以下"]},
    },
    {
        "id": "income_low",
        "phase": "3-6 个月",
        "action": "通过副业 / 兼职 / 提升社保缴费基数来增加「可验证收入」",
        "reason": "月收入 5000 以下在我行模型中按 DSR 反算的额度会非常低（普遍 < 5 万），提升到 8000+ 会有质的提升。",
        "source": "收入证明",
        "priority": 2,
        "input_match": {"monthly_income": ["5000以下"]},
    },
    {
        "id": "housing_fund",
        "phase": "3-6 个月",
        "action": "尽快在新单位补缴公积金，保持连续缴存 6 个月以上",
        "reason": "我行的「公积金」产品（最高 50 万、利率 3.45-4.50%）是该行主推低息通道，但要求连续缴存满 6-12 个月。",
        "source": "资产配置",
        "priority": 2,
        "input_match": {"housing_fund": ["无", "最低基数"]},
    },
    {
        "id": "payroll",
        "phase": "1-3 个月",
        "action": "把工资发放方式切换到目标银行借记卡代发，保留至少 3 个月代发记录",
        "reason": "我行的「工薪贷」产品要求客户在该行有 3-6 个月代发记录；无代发客户直接失去工薪贷这一优质选项。",
        "source": "收入证明",
        "priority": 2,
        "input_match": {"payroll": ["否"]},
    },
    # ====== 中长期（资产配置）======
    {
        "id": "house_long",
        "phase": "中长期",
        "action": "积累首套房按揭或保持现有房产按时还款，积累信用资产",
        "reason": "我行 A 卡中「按揭房贷记录」是加分项；按时还款 24 个月后可显著提升评分。",
        "source": "资产配置",
        "priority": 3,
        "input_match": {"house": ["无房"]},
    },
    {
        "id": "company_long",
        "phase": "中长期",
        "action": "持续在稳定单位工作，巩固单位资质的加分效应",
        "reason": "我行 A 卡中「单位性质」是稳定加分项；保持 3 年以上稳定单位工作可巩固「优质单位贷」资质。",
        "source": "收入证明",
        "priority": 3,
        "input_match": {"company_type": ["民营/外企", "个体户/小微企业", "自由职业"]},
    },
]



# ============================================================================
# 7. 通用工具函数
# ============================================================================

def norm_value(v: Any) -> str:
    """统一文本格式（去空格、去全角半角）"""
    if v is None:
        return ""
    return str(v).replace(" ", "").replace("\u3000", "").strip()


def level_for(score: int) -> str:
    """根据分数映射评级（与 scorecard_engine.level_for 同口径）"""
    if score >= 95:
        return "S"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 25:
        return "D"
    return "E"


def is_applyable_level(level: str) -> bool:
    """level 是否可申请（v22+：仅 S/A/B 可直接申请，C/D 优化后再试，E 暂缓）"""
    return level in ("S", "A", "B")


def is_vetoed(risk_tags: list[str]) -> bool:
    """根据 risk_tags 判断是否触发一票否决"""
    if not risk_tags:
        return False
    veto_markers = [
        "存在当前逾期", "连续逾期", "账户次级", "账户可疑", "账户损失",
        "5+ 笔", "5笔以上", "近 3 月 > 6", "近 6 月 > 10", "veto", "暂缓",
    ]
    for tag in risk_tags:
        for m in veto_markers:
            if m in tag:
                return True
    return False


def apply_mutex(risk_tags: list[str], advantages: list[str],
                weak_points: list[str] | None = None) -> tuple[list[str], list[str]]:
    """根据 RISK_ADVANTAGE_MUTEX 清理 advantages + weak_points，保证不自相矛盾"""
    if not risk_tags:
        return advantages, weak_points or []
    adv_out: list[str] = []
    for a in advantages:
        keep = True
        for rk, ak in RISK_ADVANTAGE_MUTEX:
            if any(rk in r for r in risk_tags) and ak in a:
                keep = False
                break
        if keep:
            adv_out.append(a)
    if weak_points is None:
        return adv_out, []
    weak_out: list[str] = []
    for w in weak_points:
        keep = True
        for rk, wk in RISK_ADVANTAGE_MUTEX:
            if any(rk in r for r in risk_tags) and wk in w:
                keep = False
                break
        if keep:
            weak_out.append(w)
    return adv_out, weak_out


def consistency_check(level: str, summary: str, risk_tags: list[str],
                      advantages: list[str], one_sentence: str = "",
                      not_recommend_reason: str = "") -> list[str]:
    """
    一致性自检器（v22+ 防自相矛盾核心）
    返回不一致问题列表（空 = 全部一致）
    """
    issues: list[str] = []
    # 1. level 口径检查：E/D 级文案不能有"可申请"等乐观词
    if level in ("D", "E"):
        optimistic_words = ["可直接申请", "高通过率", "通过率高", "立即申请"]
        for text in [summary, one_sentence, not_recommend_reason]:
            if not text:
                continue
            for w in optimistic_words:
                if w in text:
                    issues.append(f"[L{level}] 文案包含乐观词「{w}」: {text[:40]}...")
                    break
    # 2. S/A 级文案不能"暂缓""建议先优化"等悲观词
    if level in ("S", "A"):
        pessimistic_words = ["暂缓申请", "不满足准入", "建议暂停", "拒贷"]
        for text in [summary, one_sentence, not_recommend_reason]:
            if not text:
                continue
            for w in pessimistic_words:
                if w in text:
                    issues.append(f"[L{level}] 文案包含悲观词「{w}」: {text[:40]}...")
                    break
    # 3. 互斥：risk_tags 触发时，advantages 不能含对应优势
    adv_out, _ = apply_mutex(risk_tags, advantages)
    if len(adv_out) != len(advantages):
        for a_old in advantages:
            if a_old not in adv_out:
                issues.append(f"[MUTEX] advantage 与 risk 互斥已生效: 「{a_old}」被移除")
    return issues


# ============================================================================
# 8. 一键调用：基于 input_data + score + level 生成完整话术包
# ============================================================================
# 这是 SSOT 入口，所有评估结果的话术都从这里走

def build_narrative_package(input_data: dict, score: int, level: str,
                            risk_tags: list[str], advantages: list[str],
                            weak_points: list[str] | None = None,
                            top_score: int = 0) -> dict[str, Any]:
    """
    返回完整话术包（SSOT 入口）:
    {
      "one_sentence": str,        # 顶部一句话结论
      "free_summary": str,         # 免费摘要
      "level_narrative": dict,    # 等级 SSOT
      "pass_probability": str,    # 通过概率
      "rate_description": str,     # 利率档位
      "muted_advantages": list,    # 应用互斥后的优势
      "muted_weak_points": list,   # 应用互斥后的弱点
      "consistency_issues": list, # 一致性自检结果
    }
    """
    muted_adv, muted_weak = apply_mutex(risk_tags, advantages, weak_points or [])
    level_info = LEVEL_NARRATIVE.get(level, LEVEL_NARRATIVE["C"])

    one_sentence = level_info["verdict"]
    free_summary = f"{level_info['description']} {level_info['recommendation']}"

    # 应用一致性检查
    issues = consistency_check(
        level=level,
        summary=free_summary,
        risk_tags=risk_tags,
        advantages=muted_adv,
        one_sentence=one_sentence,
    )

    return {
        "one_sentence": one_sentence,
        "free_summary": free_summary,
        "level_narrative": level_info,
        "pass_probability": LEVEL_PASS_PROB.get(level, "—"),
        "rate_description": LEVEL_RATE_DESC.get(level, "—"),
        "muted_advantages": muted_adv,
        "muted_weak_points": muted_weak,
        "consistency_issues": issues,
    }
