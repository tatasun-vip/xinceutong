"""
测评路由（v3: 6 大产品独立建模 + v5 P0: business 4 维度分）

POST /api/assessment/validate           实时纠错
POST /api/assessment/submit             提交测评，6 套独立模型返回 6 个产品结果
GET  /api/assessment/free/{id}          查免费结果（综合分 + 6 产品对比前 5 个）
GET  /api/assessment/report/{id}        查完整报告（付费后才能看 6 产品详情 + 改善建议）
"""
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_current_user_optional
from app.core.exceptions import NotFoundException, ParamException
from app.database import AsyncSessionLocal, get_db
from app.models.assessment import Assessment
from app.models.bank import Bank
from app.models.scorecard import ScorecardRule
from app.models.user import User
from app.services.product_engine import (
    calculate_scores_by_product,
    synthesize_overall_score,
)
from app.services.validation_engine import validate_input
from app.utils.id_generator import gen_report_no
from app.utils.logger import logger
from app.utils.response import ok

router = APIRouter()


# ============================================================================
# 实时纠错
# ============================================================================


@router.post("/validate", summary="实时纠错校验")
async def validate_assessment(
    body: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """与 v2 保持一致"""
    step = body.get("step")
    data = body.get("data") or {}
    type_ = body.get("type", "personal")
    prev_data = body.get("prev_data") or {}

    if not step or not isinstance(step, int):
        raise ParamException("step 必须是 1-5 整数")

    merged = {**prev_data, **data}
    items = await validate_input(merged, type_, db)

    has_error = any(i["level"] == "error" for i in items)
    has_warning = any(i["level"] == "warning" for i in items)

    return ok({
        "valid": not has_error,
        "items": items,
        "has_warning": has_warning,
        "has_error": has_error,
    })


# ============================================================================
# 提交测评（v3: 6 套独立模型）
# ============================================================================


@router.post("/submit", summary="提交测评，返回 6 大产品独立结果 + 综合分")
async def submit_assessment(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict:
    """
    提交测评数据，跑 6 套独立模型，返回 6 个产品结果 + 综合分

    body: {
      type: 'personal' | 'business',
      input_data: {...},
      bank_code: 'ICBC' | null,   # 保留兼容（方法论/推广素材用）
      share_code?, promoter_code?
    }

    返回（免费版）：
      {
        assessment_id, report_no,
        overall: { score, level, limit_min, limit_max, rate_min, rate_max, pass_probability },
        product_results: [ProductResult, ...],   # 6 个产品的完整结果
        free_summary: '...',                     # 一句话摘要
        products_preview: [...],                 # 6 个产品前 2 个（兼容老版）
        is_paid: false,
        ...
      }
    """
    type_ = body.get("type", "personal")
    if type_ not in ("personal", "business"):
        raise ParamException("type 必须是 personal 或 business")
    input_data = body.get("input_data") or {}
    if not input_data:
        raise ParamException("input_data 不能为空")

    # 解析 bank_code（保留兼容，作为方法论/推广素材的关联）
    bank_id: int | None = None
    bank_code: str | None = body.get("bank_code")
    bank_name: str | None = None
    bank_features: list | None = None
    if bank_code:
        bank_row = await db.execute(
            select(Bank).where(Bank.code == bank_code, Bank.enabled == 1)
        )
        bank_obj = bank_row.scalar_one_or_none()
        if bank_obj:
            bank_id = bank_obj.id
            bank_name = bank_obj.name
            bank_features = bank_obj.features
        else:
            bank_code = None

    # 1. 跑 6 套独立模型
    product_results = await calculate_scores_by_product(input_data, type_, db)
    if not product_results:
        raise ParamException(f"未找到 user_type={type_} 的产品配置，请先执行 init_product_types.py")

    # 2. 综合分（推荐产品权重 ×1.5）
    overall_score, overall_level, limit_min, limit_max, rate_min, rate_max, pass_prob = (
        synthesize_overall_score(product_results)
    )

    # 3. 收集风险标签/优势（从所有产品的标签去重）
    all_risks: list[str] = []
    all_advs: list[str] = []
    all_weaks: list[str] = []
    for r in product_results:
        for tag in r.risk_tags:
            if tag not in all_risks:
                all_risks.append(tag)
        for tag in r.advantages:
            if tag not in all_advs:
                all_advs.append(tag)
        for tag in r.weak_points:
            if tag not in all_weaks:
                all_weaks.append(tag)

    # 4. 生成报告编号 + 落库
    report_no = gen_report_no()
    user_id = current_user.id if current_user else 0

    # 兼容字段 products（保留按等级的产品列表，给老前端用）
    products_compat = _build_products_compat(overall_level, limit_min, limit_max)

    # 完整报告 Markdown 占位（付费后填）
    full_report_md = None

    # v3.2 先聚合 top_issues + projection（在落库前算）
    top_issues = _aggregate_top_issues(input_data, all_risks, all_weaks, overall_level)
    projection = await _simulate_after_improvement(input_data, top_issues, type_, db)

    # v5 P0 4 维度分（business 专用，personal 留 None）
    # 在落库前算好，传给 Assessment 构造函数，一次 commit 落库（避免回表 + 二次 commit）
    business_dimensions = None
    if type_ == "business":
        biz_rules_q = await db.execute(
            select(ScorecardRule)
            .where(ScorecardRule.type == "business")
            .where(ScorecardRule.enabled == 1)
        )
        biz_rules = biz_rules_q.scalars().all()
        biz_rules_dict = [
            {
                "category": r.category,
                "variable": r.variable,
                "option_label": r.option_label,
                "score": float(r.score),
                "is_veto": int(r.is_veto) if r.is_veto else 0,
            }
            for r in biz_rules
        ]
        business_dimensions = _build_business_dimensions(biz_rules_dict, input_data)
        logger.info(
            f"[v5] business dimensions: total={business_dimensions.get('total')}, "
            f"compliance.ratio={business_dimensions.get('compliance', {}).get('ratio')}"
        )

    a = Assessment(
        report_no=report_no,
        user_id=user_id,
        bank_id=bank_id,
        bank_code=bank_code,
        type=type_,
        input_data=input_data,
        score=overall_score,
        level=overall_level,
        limit_min=limit_min,
        limit_max=limit_max,
        rate_min=rate_min,
        rate_max=rate_max,
        pass_probability=pass_prob,
        risk_tags=all_risks,
        advantages=all_advs,
        weak_points=all_weaks,
        suggestions=_build_suggestions(
            overall_level,
            all_risks,
            all_weaks,
            all_advs,
            input_data,
            bank_name=bank_name,
            bank_features=bank_features,
        ),
        top_issues=top_issues,
        improvement_projection=projection,
        products=products_compat,
        product_results=[r.to_dict() for r in product_results],
        dimensions=business_dimensions,  # v5 P0 4 维度分（business 专用；personal=None）
        is_paid=0,
        full_report=full_report_md,
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)

    logger.info(
        f"assessment submitted: id={a.id} no={report_no} type={type_} "
        f"score={overall_score} level={overall_level} products={len(product_results)}"
    )

    # 5. 构造返回
    # 免费版：6 个产品但只返回「摘要」（不返回详情）
    products_free_view = []
    for r in product_results:
        products_free_view.append({
            "product_code": r.product_code,
            "product_name": r.product_name,
            "product_subtitle": r.product_subtitle,
            "limit_min": r.limit_min,
            "limit_max": r.limit_max,
            "rate_min": r.rate_min,
            "rate_max": r.rate_max,
            "pass_probability": r.pass_probability,
            "level": r.level,
            "recommend": bool(r.recommend),           # 产品维度静态标志（产品页用）
            "best_for_user": bool(r.best_for_user),    # 用户维度动态推荐（报告页 ⭐ 用）
        })

    # 5. 核心问题 + 改善推演（v3.2：让免费版"看到问题但看不到解法"）
    # top_issues 和 projection 已在 a = Assessment(...) 之前算好并落库
    one_sentence = _build_one_sentence(overall_level, top_issues, projection, pass_prob)
    top_issue_free = top_issues[0] if top_issues else None

    # ============ v3.4: 报告一致性自审 + 自动修正 ============
    # 在返回前对整体数据做不变量检查，发现矛盾自动修正
    from app.services.report_auditor import audit_and_fix_report
    annual_income = 0
    try:
        income_str = input_data.get("monthly_income", "")
        income_map = {
            "5000 以下": 30000, "5000-1万": 90000, "1-2万": 180000,
            "2-3万": 300000, "3-5万": 480000, "5万以上": 720000,
        }
        annual_income = income_map.get(income_str, 0) * 12
    except Exception:
        pass

    overall_dict = {
        "score": overall_score,
        "level": overall_level,
        "limit_min": limit_min,
        "limit_max": limit_max,
        "rate_min": rate_min,
        "rate_max": rate_max,
        "pass_probability": pass_prob,
    }
    overall_dict, one_sentence, top_issues, projection, audit = audit_and_fix_report(
        overall=overall_dict,
        one_sentence=one_sentence,
        top_issues=top_issues,
        projection=projection,
        annual_income=annual_income,
    )
    # 修正后回写到局部变量（保证数据库和返回一致）
    overall_level = overall_dict["level"]
    limit_min = overall_dict["limit_min"]
    limit_max = overall_dict["limit_max"]
    rate_min = overall_dict["rate_min"]
    rate_max = overall_dict["rate_max"]
    pass_prob = overall_dict["pass_probability"]
    # 同步更新数据库（如果之前持久化了不一致的数据）
    a.level = overall_level
    a.limit_min = limit_min
    a.limit_max = limit_max
    a.rate_min = rate_min
    a.rate_max = rate_max
    a.pass_probability = pass_prob
    if projection is not None:
        a.improvement_projection = projection

    # ============ v5 P0: business 4 维度分 已在 db.commit 之前算好（见 line 158 之后）============
    if audit.has_issue or audit.fixes:
        logger.warning(
            f"[AUDIT] id={a.id} issues={audit.issues} fixes={audit.fixes}"
        )

    return ok({
        "assessment_id": a.id,
        "report_no": a.report_no,
        "overall": overall_dict,
        "one_sentence": one_sentence,
        "top_issue_free": top_issue_free,    # 免费版只露 1 个核心问题
        "top_issues_total": len(top_issues), # 全部核心问题数（用于文案"X 个问题"）
        "projection": projection,             # 改善后推演（用于"改善后预计通过 X"）
        "free_summary": _build_free_summary(overall_level, limit_min, limit_max, pass_prob),
        "product_results": products_free_view,   # 免费版 6 个产品摘要
        "is_paid": False,
        "paid_at": None,
        "veto_count": sum(1 for r in product_results if r.veto is not None),
        "dimensions": None,    # v5 P0 已临时回滚（model 字段 + 计算逻辑都已注释）
    })


def _build_free_summary(level: str, limit_min: int, limit_max: int, pass_prob: str) -> str:
    """根据综合分生成 1-2 句免费摘要"""
    if level in ("S", "A"):
        return (
            f"您是 {level} 级优质客户，模拟可获额度 {limit_min // 10000}-{limit_max // 10000} 万元，"
            f"通过率 {pass_prob}。"
        )
    if level == "B":
        return (
            f"您是 {level} 级良好客户，模拟可获额度 {limit_min // 10000}-{limit_max // 10000} 万元，"
            f"通过率 {pass_prob}。"
        )
    if level == "C":
        return (
            f"您是 {level} 级一般客户，模拟可获额度 {limit_min // 10000}-{limit_max // 10000} 万元，"
            f"建议先优化再申请。"
        )
    if level == "D":
        return "您是 D 级较弱客户，建议先改善征信 / 收入后再申请。"
    return "当前情况不满足模拟准入条件，建议先解决风险项。"


# ============================================================================
# v5 P0: business 4 维度分计算
# ============================================================================

# 4 维度权重（合计 100%；与前端 4 维度预览块完全对应）
_BIZ_DIM_WEIGHT = {
    "legal_person": 0.30,  # 法人画像
    "enterprise":   0.40,  # 企业画像
    "compliance":   0.20,  # 合规风险
    "industry":     0.10,  # 行业景气
}


def _build_business_dimensions(rules: list[dict], input_data: dict) -> dict:
    """business 4 维度分（v5 P0）

    输入：
      rules: ScorecardRule 字典列表（type=business, enabled=1）
      input_data: 用户填写数据

    输出：
      {
        "legal_person": {"raw": 14, "max": 18, "ratio": 77.8, "weight": "30%", "weighted": 23.34},
        "enterprise":   {"raw": 48, "max": 60, "ratio": 80.0, "weight": "40%", "weighted": 32.0},
        "compliance":   {"raw": 20, "max": 20, "ratio": 100.0,"weight": "20%", "weighted": 20.0},
        "industry":     {"raw":  8, "max": 10, "ratio": 80.0, "weight": "10%", "weighted":  8.0},
        "total": 83.34
      }
    """
    from app.services.scorecard_engine import _score_items

    # 1. 跑逐项打分
    _raw, items = _score_items(rules, input_data)

    # 2. 索引：variable → category, variable → max score
    var_to_cat: dict[str, str] = {}
    var_max_score: dict[str, float] = {}
    for r in rules:
        if r.get("is_veto") == 1:
            continue
        var = r["variable"]
        cat = r.get("category")
        if cat is None:
            continue
        var_to_cat[var] = cat
        if var not in var_max_score or float(r["score"]) > var_max_score[var]:
            var_max_score[var] = float(r["score"])

    # 3. 维度 max = 维度内各 variable 的 max 之和
    cat_max: dict[str, float] = {k: 0.0 for k in _BIZ_DIM_WEIGHT}
    for var, mxs in var_max_score.items():
        cat = var_to_cat[var]
        if cat in cat_max:
            cat_max[cat] += mxs

    # 4. 汇总各维度 raw（按命中项）
    cat_raw: dict[str, float] = {k: 0.0 for k in _BIZ_DIM_WEIGHT}
    for it in items:
        cat = var_to_cat.get(it["variable"])
        if cat in cat_raw:
            cat_raw[cat] += float(it["score"])

    # 5. 输出
    result: dict = {}
    total = 0.0
    for cat in ["legal_person", "enterprise", "compliance", "industry"]:
        raw = cat_raw[cat]
        mx = cat_max[cat] if cat_max[cat] > 0 else 1.0  # 避免除 0
        ratio = round(raw / mx * 100, 1)
        w = _BIZ_DIM_WEIGHT[cat]
        weighted = round(ratio * w, 2)
        result[cat] = {
            "raw": raw,
            "max": mx,
            "ratio": ratio,
            "weight": f"{int(w * 100)}%",
            "weighted": weighted,
        }
        total += weighted
    result["total"] = round(total, 1)
    return result


# ============================================================================
# 核心问题聚合（按严重度排序，最多 3 个）
# ============================================================================
# 严重度排序权重（用于 top_issues 排序）
_ISSUE_SEV_RANK = {"high": 3, "mid": 2, "low": 1}

# 严重度对应的视觉颜色（前端可读 hex）
_ISSUE_SEV_COLOR = {"high": "#C62828", "mid": "#EF6C00", "low": "#C9A96E"}

# 改善模板库：每条核心问题都按"5 维度"展开（是什么/为什么/影响/怎么改/预期）
# key = 检测关键词（命中 risk_tag/weak_point 文本包含的子串）
# input_match = 可选，input_data 字段值匹配规则（field, [允许值列表]）
_ISSUE_TEMPLATES: list[dict] = [
    # === 征信类 ===
    {
        "key": "近 3 个月查询",
        "category": "征信",
        "title": "近期征信查询过于频繁",
        "what": "近 3 个月内，您的征信报告上有多次贷款 / 信用卡的「硬查询」记录。",
        "why": "银行 A 卡模型中，近 3 个月硬查询是核心风控指标。每多一次申请都意味着「资金紧张」信号，6 次以上几乎会被自动拦截。",
        "impact_prob": "通过概率下降 25%-40%",
        "impact_amount": "额度下调 20%-30%",
        "impact_rate": "年化利率上浮 1%-2%",
        "how": "立即停止所有贷款、信用卡、分期申请；90 天后查询记录按月滚动消失，影响自然消除。",
        "when": "未来 90 天",
        "result": "90 天后查询痕迹淡出，通过概率预计回升 20-30 个百分点。",
        "fix_fields": {"recent_3month_queries": "0-2次"},
        "input_match": {"recent_3month_queries": ["6次以上"]},
    },
    {
        "key": "信用卡使用率",
        "category": "征信",
        "title": "信用卡使用率偏高",
        "what": "您的信用卡已用额度占总额度的 80% 以上。",
        "why": "使用率超 80% 在银行评分卡里等于「高资金需求 + 潜在违约」——模型直接降一档。",
        "impact_prob": "通过概率下降 15%-25%",
        "impact_amount": "额度下调 15%-20%",
        "impact_rate": "—",
        "how": "账单日前还部分欠款，把使用率压到 50% 以下；建议长期保持 30% 以下。",
        "when": "未来 1-2 个月（次账单日后即生效）",
        "result": "使用率压到 30% 后，通过概率预计回升 10-20 个百分点。",
        "fix_fields": {"credit_card_usage": "30%以下"},
        "input_match": {"credit_card_usage": ["50-80%", "80%以上"]},
    },
    {
        "key": "在贷笔数",
        "category": "征信",
        "title": "在贷笔数偏多",
        "what": "您当前有较多未结清的贷款账户（≥3 笔）。",
        "why": "在贷笔数多被判定为「多头借贷」——银行认为您在多家机构间周转资金，还款压力大。",
        "impact_prob": "通过概率下降 20%-30%",
        "impact_amount": "额度下调 25%-40%",
        "impact_rate": "年化利率上浮 1%-2%",
        "how": "优先结清金额最小的 1-2 笔（如某笔消费分期），把笔数降到 3 笔以内。",
        "when": "未来 1-3 个月",
        "result": "笔数压到 3 笔以内后，部分产品可通过率回升 15-25 个百分点。",
        "fix_fields": {"loan_count": "1-2笔"},
        "input_match": {"loan_count": ["3笔以上"]},
    },
    {
        "key": "当前逾期",
        "category": "征信",
        "title": "存在当前逾期",
        "what": "您的征信报告显示存在当前未结清的逾期记录。",
        "why": "「当前逾期」是几乎所有银行的一票否决项，命中即直接拒批。",
        "impact_prob": "通过概率降至 0",
        "impact_amount": "额度直接归零",
        "impact_rate": "—",
        "how": "立即结清所有逾期欠款；还清次月向央行申请更新征信报告。",
        "when": "未来 1-2 个月（结清 + 报告更新）",
        "result": "结清后 30-60 天，逾期标记从「当前逾期」变为「历史逾期」，影响逐步淡化。",
        "fix_fields": {"current_overdue": "无"},
    },
    {
        "key": "近 2 年累计逾期",
        "category": "征信",
        "title": "近 2 年逾期次数较多",
        "what": "近 2 年内您的征信报告上有 3 次以上逾期记录。",
        "why": "银行模型中逾期次数是「违约历史」的核心量化指标，3 次以上直接降 D/E 级。",
        "impact_prob": "通过概率下降 30%-50%",
        "impact_amount": "额度下调 30%-50%",
        "impact_rate": "年化利率上浮 1%-3%",
        "how": "保持所有账户按时还款满 24 个月，逾期记录逐步滚动出 2 年观察窗。",
        "when": "未来 24 个月",
        "result": "24 个月无新增逾期后，2 年窗口滚动清空，评分恢复至正常档位。",
        "fix_fields": {"overdue_2year": "0次"},
    },
    # === 收入类 ===
    {
        "key": "月收入较低",
        "category": "收入",
        "title": "月收入水平偏低",
        "what": "您的月收入在该行模型中处于偏低区间。",
        "why": "月收入直接决定该行愿意给的额度上限与利率档位——收入偏低则额度天花板低。",
        "impact_prob": "通过概率下降 10%-20%",
        "impact_amount": "额度上限受限 30%-50%",
        "impact_rate": "利率上浮 0.5%-1%",
        "how": "提升副业 / 兼职收入并提供连续 6 个月的银行流水；或转入更高收入的工作。",
        "when": "未来 3-6 个月",
        "result": "月收入提升到当前 1.5 倍后，额度天花板相应提升 20-40%。",
        "fix_fields": {"monthly_income": "2万-3万"},
    },
    {
        "key": "社保",
        "category": "收入",
        "title": "社保 / 代发不连续",
        "what": "您的社保或代发工资记录连续性不足。",
        "why": "社保和代发是银行验证「真实收入」的核心凭证，不连续 = 收入不稳定。",
        "impact_prob": "通过概率下降 15%-25%",
        "impact_amount": "额度下调 20%-30%",
        "impact_rate": "—",
        "how": "通过合规渠道补缴社保；保持代发工资连续 6 个月以上。",
        "when": "未来 3-6 个月",
        "result": "社保 / 代发连续 6 个月后，模型将「收入稳定」项分数拉满。",
        "fix_fields": {"social_security": "连续 3 年以上", "payroll": "是"},
    },
    # === 资产类 ===
    {
        "key": "无房",
        "category": "资产",
        "title": "无房产可作担保",
        "what": "您目前名下无房产（或有按揭未结清）。",
        "why": "「有房客户贷」等主打资产的产品需要房产作为担保 / 加分项；无房直接被排除。",
        "impact_prob": "部分产品直接拒批",
        "impact_amount": "失去 1-2 个有竞争力的产品选项",
        "impact_rate": "—",
        "how": "短期内难以解决；可优先选择「不依赖房产」的产品（如优质单位贷 / 公积金贷）。",
        "when": "中长期的资产积累",
        "result": "无需等待改善；调整申请策略，改投不依赖房产的产品。",
        "fix_fields": {},  # 资产类问题无短期解，标记为空
    },
    {
        "key": "无按揭",
        "category": "资产",
        "title": "无按揭房贷记录",
        "what": "您目前没有按揭房贷记录。",
        "why": "长期按时还房贷是最强的「信用资产证明」——缺失会让模型少一项关键加分。",
        "impact_prob": "通过概率下降 5%-10%",
        "impact_amount": "额度下调 10%-15%",
        "impact_rate": "—",
        "how": "通过其他长期信用账户（信用卡 / 消费贷）按时还款满 24 个月来积累信用资产。",
        "when": "未来 24 个月",
        "result": "24 个月按时还款记录积累后，模型中「信用历史」项会显著提升。",
        "fix_fields": {"house": "无按揭"},
    },
    # === 单位 / 基础类 ===
    {
        "key": "单位性质",
        "category": "基础",
        "title": "工作单位性质不占优",
        "what": "您的工作单位不在该行「白名单」内（如非公务员 / 事业单位 / 国企 / 央企）。",
        "why": "「优质单位贷」对单位性质有严格要求——非名单内单位直接被排除在该产品外。",
        "impact_prob": "失去 1 个低利率产品",
        "impact_amount": "—",
        "impact_rate": "利率上浮 1%-2%",
        "how": "短期内无法改变；建议改投「工薪贷」「公积金贷」等不卡单位的产品。",
        "when": "—",
        "result": "调整申请策略即可；其他产品仍可正常评估。",
        "fix_fields": {},
    },
    {
        "key": "工作年限",
        "category": "基础",
        "title": "工作年限较短",
        "what": "您当前工作年限不足 1 年。",
        "why": "工龄 < 1 年被判定为「收入不稳定」，是稳定性指标的核心扣分项。",
        "impact_prob": "通过概率下降 15%-25%",
        "impact_amount": "额度下调 20%-30%",
        "impact_rate": "—",
        "how": "保持当前工作 6-12 个月后再申请；或提供上一份工作的延续性证明。",
        "when": "未来 6-12 个月",
        "result": "工龄累计到 1-3 年后，稳定性指标回升到正常档位。",
        "fix_fields": {"work_years": "1-3年"},
        "input_match": {"work_years": ["不足1年"]},
    },
]


def _aggregate_top_issues(
    input_data: dict,
    risk_tags: list[str],
    weak_points: list[str],
    overall_level: str,
    max_n: int = 3,
) -> list[dict]:
    """
    从 risk_tags / weak_points / input_data 中聚合「核心问题」列表，按严重度排序。

    返回结构：
      [{
        "id": 1,
        "title": "近期征信查询过于频繁",
        "category": "征信",
        "severity": "high" | "mid" | "low",
        "severity_color": "#C62828",
        "impact_prob": "通过概率下降 25%-40%",
        "impact_amount": "额度下调 20%-30%",
        "impact_rate": "年化利率上浮 1%-2%",
        "what": "...",
        "why": "...",
        "how": "...",
        "when": "未来 90 天",
        "result": "...",
        "fixable_in_90d": bool,    # 短期内能否解决（影响推演计算）
      }, ...]
    """
    candidates: list[dict] = []
    seen_titles: set[str] = set()

    # 文本拼接用于关键词匹配
    text_blob = " | ".join(risk_tags + weak_points)

    # 1. 模板匹配（按模板顺序）
    for tpl in _ISSUE_TEMPLATES:
        if tpl["title"] in seen_titles:
            continue
        # 命中条件：
        #   a) 模板 key 出现在 risk_tag/weak_point 文本中
        #   b) input_data 字段值匹配 input_match 规则
        matched = tpl["key"] in text_blob
        if not matched and tpl.get("input_match"):
            for field, allowed in tpl["input_match"].items():
                if input_data.get(field) in allowed:
                    matched = True
                    break

        if matched:
            # 严重度判断
            sev = "mid"
            if tpl["key"] in ("当前逾期", "近 3 个月查询", "近 2 年累计逾期", "在贷笔数"):
                sev = "high"
            elif tpl["key"] in ("信用卡使用率", "月收入较低", "社保", "工作年限"):
                sev = "mid"
            else:
                sev = "low"

            # 短期能否解决：fix_fields 非空 + 关键类问题
            fixable = bool(tpl.get("fix_fields")) and tpl["key"] not in (
                "无房", "无按揭", "单位性质",  # 这些没 90 天短期解
            )

            candidates.append({
                **tpl,
                "id": 0,  # 后面再排序重排
                "severity": sev,
                "severity_color": _ISSUE_SEV_COLOR[sev],
                "fixable_in_90d": fixable,
            })
            seen_titles.add(tpl["title"])

    # 2. E 级兜底：若没匹配到任何 issue 但 overall 是 E，补一条通用 E 级问题
    if overall_level == "E" and not candidates:
        candidates.append({
            "id": 1,
            "title": "当前资质不满足模拟准入",
            "category": "基础",
            "severity": "high",
            "severity_color": _ISSUE_SEV_COLOR["high"],
            "what": "您的整体资质未达到模拟准入门槛——可能存在当前逾期、严重账户异常、连续逾期等任一情况。",
            "why": "银行准入模型对「当前逾期 / 黑名单 / 次级账户」等硬性条件是 0 容忍，命中即直接拒批。",
            "impact_prob": "通过概率降至 0",
            "impact_amount": "暂无额度",
            "impact_rate": "—",
            "how": "建议先到央行打印详版征信报告（人行官网 / 线下网点），逐条核实风险来源后解决。",
            "when": "未来 1-3 个月",
            "result": "消除所有硬性风险项后，重新测评预计回到 D 级以上。",
            "fixable_in_90d": False,
        })

    # 3. 排序：severity desc + impact 降序
    candidates.sort(
        key=lambda x: (
            _ISSUE_SEV_RANK.get(x["severity"], 0),
            # 影响大者优先（"下降 X" 中 X 大的优先）—— 简单按关键词判断
            1 if "30%-50%" in x["impact_prob"] or "降至 0" in x["impact_prob"] else 0,
        ),
        reverse=True,
    )

    # 4. 截断 + 重排 id
    top = candidates[:max_n]
    for i, c in enumerate(top, start=1):
        c["id"] = i

    return top


def _build_one_sentence(
    overall_level: str,
    top_issues: list[dict],
    projection: dict | None,
    pass_probability: str = "",
) -> str:
    """
    生成"一句话结论"（报告顶部 + 付费按钮文案共用）

    优先级（按综合级别严格区分，避免"基本符合"等自相矛盾措辞）：
      1. E 级 或 有 high 严重问题 → "建议暂缓，先优化 N 个核心问题"
      2. D 级（较弱）            → 诚实告诉用户"目前较弱、通过率偏低"，给出具体方向
      3. C 级（一般）            → "资质一般，建议先优化再申请"
      4. B 级（良好）            → "资质良好，可尝试申请通过率较高的产品"
      5. S/A 级                  → "资质优质，可直接申请"
    """
    n_high = sum(1 for i in top_issues if i.get("severity") == "high")
    n_mid = sum(1 for i in top_issues if i.get("severity") == "mid")
    n_total = len(top_issues)
    n_low = sum(1 for i in top_issues if i.get("severity") == "low")

    # ====== L1: E 级 或 high 严重问题 → 暂缓 ======
    if overall_level == "E" or n_high >= 1:
        return f"建议暂缓申请，先优化 {n_total} 个核心问题"

    # ====== L2: D 级（较弱）→ 诚实描述 + 给出方向 ======
    # 不要再用"基本符合"等自相矛盾措辞
    if overall_level == "D":
        # 有可改善推演：给用户"通过率可提升"的预期
        if projection and projection.get("score", 0) > 0 and projection.get("level") not in ("", "E", "D"):
            target = projection.get("level", "")
            return f"目前 {overall_level} 级较弱，先优化 {n_total} 个问题，预计可达 {target} 级"
        if n_mid >= 1 or n_low >= 1:
            return f"目前 {overall_level} 级较弱，先优化 {n_total} 个问题后再申请更稳妥"
        return f"目前 {overall_level} 级较弱，建议先优化 {n_total} 项关键指标再申请"

    # ====== L3: C 级（一般）→ 有提升空间 ======
    if overall_level == "C":
        if projection and projection.get("level") in ("A", "B"):
            target = projection.get("level", "")
            return f"资质一般，先优化 {n_total} 个问题，预计可达 {target} 级"
        return f"您的资质一般，建议先优化 {n_total} 项指标再申请"

    # ====== L4: B 级（良好）→ 谨慎乐观 ======
    if overall_level == "B":
        if pass_probability in ("高", "中高"):
            return "您的资质良好，可优先选择通过率较高的产品申请"
        return f"您的资质尚可，但通过率偏低，建议先优化 {n_total} 个细节再申请"

    # ====== L5: S/A 级（优质）→ 自信推荐 ======
    if overall_level in ("S", "A"):
        return "您的资质已属优质，可直接申请"

    # ====== 兜底（理论上不会到这里）======
    return f"您的资质处于 {overall_level} 级，建议参考完整报告"


async def _simulate_after_improvement(
    input_data: dict,
    top_issues: list[dict],
    type_: str,
    db: AsyncSession,
) -> dict | None:
    """
    模拟"按建议执行 90 天后"的结果。

    逻辑：把高严重度问题的 fix_fields 应用到 input_data，再跑一遍 calculate_scores_by_product。
    返回：{
        score, level, limit_min, limit_max, pass_probability, pass_rank,
        period_days, fixed_count
    }

    若 top_issues 为空 / 全部不可改善 → 返回 None
    """
    fixable = [i for i in top_issues if i.get("fixable_in_90d")]
    if not fixable:
        return None

    # 1. 构造"改善后"的 input_data（应用每个 fixable issue 的 fix_fields）
    improved = dict(input_data)
    for issue in fixable:
        for field, val in issue.get("fix_fields", {}).items():
            if field in improved:
                improved[field] = val

    # 2. 重新跑 6 套产品
    try:
        new_results = await calculate_scores_by_product(improved, type_, db)
    except Exception as e:
        logger.warning(f"改善后推演失败: {e}")
        return None

    if not new_results:
        return None

    # 3. 算综合分
    new_score, new_level, new_limit_min, new_limit_max, _, _, new_pass_prob = (
        synthesize_overall_score(new_results)
    )

    # 4. 通过概率等级权重（用于排序比较）
    _RANK = {"高": 5, "中高": 4, "中": 3, "低": 2, "极低": 1}
    return {
        "score": new_score,
        "level": new_level,
        "limit_min": new_limit_min,
        "limit_max": new_limit_max,
        "pass_probability": new_pass_prob,
        "pass_rank": _RANK.get(new_pass_prob, 0),
        "period_days": 90,
        "fixed_count": len(fixable),
    }


def _build_products_compat(level: str, limit_min: int, limit_max: int) -> list[dict]:
    """兼容老版按等级的产品列表（老 free.vue 用）"""
    products_by_level: dict[str, list[dict]] = {
        "S": [
            {"name": "公积金优享贷", "pass": "高", "recommend": True},
            {"name": "工资代发极速贷", "pass": "高"},
            {"name": "白领信用贷", "pass": "高"},
        ],
        "A": [
            {"name": "公积金优享贷", "pass": "高", "recommend": True},
            {"name": "工资代发极速贷", "pass": "中高"},
            {"name": "白领信用贷", "pass": "中高"},
        ],
        "B": [
            {"name": "工薪贷", "pass": "中高", "recommend": True},
            {"name": "公积金贷", "pass": "中"},
        ],
        "C": [
            {"name": "消费分期", "pass": "中", "recommend": True},
            {"name": "小额信贷", "pass": "中"},
        ],
        "D": [
            {"name": "小额信贷", "pass": "低", "recommend": True},
        ],
        "E": [
            {"name": "暂无可推荐产品", "pass": "极低"},
        ],
    }
    raw_list = products_by_level.get(level, products_by_level["E"])
    return [
        {
            "name": p["name"],
            "limit": (
                f"¥{limit_min // 10000}万 ~ ¥{limit_max // 10000}万"
                if limit_max >= 10000
                else f"¥{limit_min} ~ ¥{limit_max}"
            ),
            "pass": p["pass"],
            "recommend": p.get("recommend", False),
        }
        for p in raw_list
    ]


def _build_suggestions(
    level: str,
    risks: list[str],
    weaks: list[str],
    advs: list[str],
    input_data: dict | None = None,
    bank_name: str | None = None,
    bank_features: list[str] | None = None,
) -> list[dict[str, str]]:
    """
    根据综合分、风险标签、弱点、用户优势、目标银行特色生成改善建议。

    返回: [{period, action, reason, source}, ...]
      - period: 立即 / 1-3 个月 / 3-6 个月 / 6 个月+ / 持续
      - action: 具体行动
      - reason: 为什么这样做（基于该行模型）
      - source: 所属维度（征信修复 / 收入证明 / 资产配置 / 申请策略 / 日常习惯）

    设计原则：
      1. 每条建议都引用用户实际填写的数据（不让用户读「通用鸡汤」）
      2. 按时间排序，最多 8 条；按「立即 → 1-3 月 → 3-6 月 → 6 月+ → 持续 → 申请策略」组织
      3. 该行重视什么，就把对应建议排在前面、并把「理由」挂上该行偏好
    """
    input_data = input_data or {}
    bank_label = bank_name or "目标银行"
    focus_kw = _bank_focus_keywords(bank_features or [])
    focus_hint = _focus_to_phrase(focus_kw)
    suggestions: list[dict[str, str]] = []
    seen_actions: set[str] = set()

    def add(period: str, action: str, reason: str, source: str) -> None:
        """去重添加建议（action 主文本相同则跳过）"""
        key = action.strip()[:32]
        if key in seen_actions:
            return
        seen_actions.add(key)
        suggestions.append(
            {"period": period, "action": action, "reason": reason, "source": source}
        )

    # ========================================================================
    # Phase 1: 立即（致命问题 — 命中就一票否决）
    # ========================================================================
    if input_data.get("current_overdue") == "有":
        add(
            "立即",
            "结清当前所有逾期欠款，并在还清后次月向央行申请更新征信报告",
            f"{bank_label}的准入模型把「当前逾期」列为硬性一票否决项，未结清前任何申请都会被系统秒拒。",
            "征信修复",
        )
    if input_data.get("serial_overdue") == "有":
        add(
            "立即",
            "联系贷款机构说明情况并制定结清计划，避免「连续逾期」标记继续累计",
            f"连续 60 天以上逾期在 {bank_label} 模型中权重极高，会被判定为「严重信用瑕疵」，需 24 个月才能逐步淡化。",
            "征信修复",
        )
    if input_data.get("bad_status") == "有":
        add(
            "立即",
            "到央行打印详版征信报告，确认次级/可疑/损失账户来源并结清",
            f"{bank_label}对账户状态为「次级/可疑/损失」的客户直接判 D/E 级，需先消除五级分类异常。",
            "征信修复",
        )

    # ========================================================================
    # Phase 2: 1-3 个月（短期优化 — 高频查询 / 信用卡使用率 / 在贷笔数）
    # ========================================================================
    if "近 3 个月查询过多" in risks or input_data.get("recent_3month_queries") == "6次以上":
        add(
            "1-3 个月",
            "停止申请任何贷款 / 信用卡 / 分期，让征信报告上「贷款审批」硬查询自然衰减",
            f"{bank_label}的 A 卡对近 3 个月硬查询非常敏感，6 次以上几乎会被风控拦截；查询记录按月滚动消失。",
            "征信修复",
        )
    if "信用卡使用率过高" in risks or input_data.get("credit_card_usage") == "80%以上":
        add(
            "1-3 个月",
            "还部分信用卡欠款，把使用率压到 50% 以下（建议在账单日前还）",
            f"信用卡使用率超 80% 在 {bank_label}模型里等于「高资金需求 + 潜在违约」，是评分掉档的重要扣分项。",
            "征信修复",
        )
    if "在贷笔数偏多" in risks or input_data.get("loan_count") == "5笔以上":
        add(
            "1-3 个月",
            "优先结清金额最小的 1-2 笔在贷，把笔数降到 3 笔以内",
            f"{bank_label}的 A 卡在「在贷笔数」上做了非线性惩罚，3 笔以内属于正常区间，5 笔以上直接拉低一档。",
            "征信修复",
        )
    if "近 2 年有逾期" in risks or input_data.get("overdue_2year") in ("1-3次", "3次以上"):
        add(
            "1-3 个月",
            "近 2 年的逾期记录无法消除，但保持 24 个月无逾期可显著淡化影响",
            f"逾期记录在 {bank_label}模型中按「近 2 年窗口」评估，保持 24 个月干净记录后该维度权重自动降为 0。",
            "征信修复",
        )

    # ========================================================================
    # Phase 3: 3-6 个月（中期建设 — 白户/工作年限/收入流水）
    # ========================================================================
    if "白户风险（无信贷记录）" in risks or input_data.get("white_account") == "是":
        add(
            "3-6 个月",
            "先申请 1 张信用卡并正常使用 3-6 个月，建立信贷历史",
            f"白户在 {bank_label}模型中只能拿到「基础分」，因缺乏还款历史无法被系统信任；建好首张卡后再申请额度会显著提升。",
            "征信修复",
        )
    if "工作年限较短" in weaks or input_data.get("work_years") == "1年以下":
        add(
            "3-6 个月",
            "保持当前工作至满 1 年再申请，期间让社保 / 公积金持续缴存",
            f"{bank_label}的「工作稳定性」维度 1 年是分水岭，1 年以下在评分卡里被压一档；满 1 年后该维度满权重。",
            "收入证明",
        )
    if "月收入偏低" in weaks or input_data.get("monthly_income") == "5000以下":
        add(
            "3-6 个月",
            "通过副业 / 兼职 / 提升社保缴费基数来增加「可验证收入」",
            f"月收入 5000 以下在 {bank_label}模型中按 DSR 反算的额度会非常低（普遍 < 5 万），提升到 8000+ 会有质的提升。",
            "收入证明",
        )

    # ========================================================================
    # Phase 4: 银行特性优化（公积金/代发/房/小微 — 按目标银行特色生成）
    # ========================================================================
    # 公积金
    if "公积金" in focus_kw and input_data.get("housing_fund") in ("无", "最低基数"):
        if "公积金连续缴存" not in advs:
            add(
                "3-6 个月",
                "尽快在新单位补缴公积金，保持连续缴存 6 个月以上",
                f"{bank_label}的「公积金」产品（最高 50 万、利率 3.45-4.5%）是该行主推低息通道，但要求连续缴存满 6-12 个月。",
                "资产配置",
            )
    # 代发
    if "代发工资" in focus_kw and input_data.get("payroll") == "否":
        if "工资代发" not in advs:
            add(
                "1-3 个月",
                "把工资发放方式切换到该行借记卡代发，保留至少 3 个月代发记录",
                f"{bank_label}对代发工资客户有专属授信通道：同条件下额度 +30%、利率下浮 10-15%，代发记录是关键门槛。",
                "收入证明",
            )
    # 房产
    if "房产" in focus_kw:
        if input_data.get("house") == "无房":
            add(
                "持续",
                "该行最看重房产，无房客户建议优先考虑「建行以外的互联网银行（如微众/网商）」",
                f"{bank_label}的核心低息产品线（房产抵押贷 / 快贷）以房产为重要准入条件，无房客户走该行通过率会显著低于其他产品。",
                "申请策略",
            )
        elif input_data.get("house") == "有按揭" and "本地有房" not in advs:
            add(
                "3-6 个月",
                "如有提前还款能力可结清房贷，把「无按揭」作为下一次申请的加分项",
                f"{bank_label}模型对「无按揭」客户给的资产抵押率比「有按揭」高 15-20%，直接影响有房客户贷额度上限。",
                "资产配置",
            )
    # 存量客户
    if "存量客户" in focus_kw and "已有客户" not in str(advs):
        add(
            "1-3 个月",
            "优先在该行开立一张储蓄卡并保持 1-3 个月流水，提升「存量客户」权重",
            f"{bank_label}对存量白名单客户有内部授信加成（额度 +20-30%、利率下浮 5-10%），先建关系再申请会更划算。",
            "申请策略",
        )
    # 小微 / 电商
    if "小微/电商流水" in focus_kw:
        add(
            "持续",
            "保持淘宝/天猫/抖音店铺的持续经营流水，季度营收稳定增长可触发提额",
            f"{bank_label}的小微贷模型重点看「近 12 个月流水」和「经营连续性」，月流水稳定 10 万+ 是拿到高额度的关键。",
            "收入证明",
        )
    # 审批快
    if "审批快" in focus_kw and "工资代发" not in advs:
        add(
            "1-3 个月",
            "先在该行手机银行 APP 申请一张储蓄卡 + 一笔小额理财，建立基础关系后再走信贷",
            f"{bank_label}的「审批快」产品对存量关系户有内部白名单加成，纯新户首贷通过率会低于已建关系客户。",
            "申请策略",
        )
    # 高额度
    if "高额度" in focus_kw and input_data.get("monthly_income") in ("5000以下", "5000-8000"):
        add(
            "3-6 个月",
            "通过副业 / 兼职 / 经营流水把月可验证收入提升到 1.5 万+",
            f"{bank_label}以「高额度」为核心卖点，但起批门槛通常要求月收入 1.5 万+，否则最高额度会被自动压档。",
            "收入证明",
        )
    # 保险
    if "保险" in focus_kw and "保险客户" not in str(advs):
        add(
            "持续",
            "持有该行/该公司保险满 2 年后再申请信贷，保单贷产品有专属授信加成",
            f"{bank_label}的「保单贷」是其特色产品，要求持有保单满 2 年；提前配置比临时抱佛脚更划算。",
            "资产配置",
        )
    # 外汇
    if "外汇" in focus_kw and input_data.get("housing_fund") in ("无", "最低基数"):
        add(
            "持续",
            "该行传统优势是外汇 / 外贸客群，普通工薪客户走该行通过率不一定最优",
            f"{bank_label}在外汇业务和外贸企业有专项授信通道，如果您没有境外收入或外贸背景，可考虑改申请其他行。",
            "申请策略",
        )
    # 通用弱项：储蓄
    if input_data.get("deposit") == "无":
        add(
            "3-6 个月",
            "每月固定储蓄收入的 20-30%，积累 6 个月后能显著提升评分",
            f"{bank_label}的 A 卡在「金融资产」维度上，无存款客户会丢 5-10 分；积累到 10 万+ 即可进入高分区间。",
            "资产配置",
        )

    # ========================================================================
    # Phase 5: 申请策略（按等级）
    # ========================================================================
    if level == "S":
        match_phrase = (
            f"，{bank_label}的\"{focus_hint}\"偏好与您匹配度高"
            if focus_hint
            else ""
        )
        add(
            "1-3 个月",
            "同时申请 2-3 家头部银行的低息产品（建行快贷 / 工行融e借 / 招行闪电贷），择优放款",
            f"您当前为 S 级{match_phrase}，建议同步申请 2-3 家以拿到最低利率组合。",
            "申请策略",
        )
    elif level == "A":
        if "代发" in focus_kw:
            add(
                "1-3 个月",
                "优先申请「代发工资对应行」的产品，再考虑其他 1-2 家",
                f"您为 A 级，{bank_label}对您匹配的代发/已有客户产品有 30% 额度加成，先用满再外扩。",
                "申请策略",
            )
        else:
            add(
                "1-3 个月",
                "可申请 1-2 家银行信贷，避免短期内多头申请拉低评级",
                f"您为 A 级，建议先在 {bank_label} 申请主推产品，通过后再尝试其他 1 家。",
                "申请策略",
            )
    elif level == "B":
        add(
            "1-3 个月",
            "先在 1 家通过率较高的银行试申请（如工资代发行 / 公积金行），通过后再尝试其他",
            f"您为 B 级，{bank_label}的通过率为中高，{('匹配「' + focus_hint + '」维度') if focus_hint else '建议先建关系后申请'}，通过率会更高。",
            "申请策略",
        )
    elif level == "C":
        add(
            "1-3 个月",
            "建议先申请 1 家通过率中等的银行（如股份制商业银行），通过后再尝试提额",
            f"您为 C 级，{bank_label}的通过率约中，建议先建立第一笔信贷记录，6 个月后再次申请可显著提升评分。",
            "申请策略",
        )
    elif level in ("D", "E"):
        add(
            "立即",
            "暂缓申请任何贷款 / 信用卡，先解决以上征信 / 收入问题",
            f"您当前为 {level} 级，{bank_label}的模型通过率为「低/极低」，强行申请会留下更多硬查询和拒贷记录，进一步恶化征信。",
            "申请策略",
        )

    # ========================================================================
    # Phase 6: 持续（兜底 — 日常习惯）
    # ========================================================================
    add(
        "持续",
        "保持按时还款 / 不逾期 / 信用卡使用率 ≤ 50% / 半年内不办新卡",
        f"{bank_label}及主流银行的 A 卡在「近 24 个月还款记录」上权重最高 30%，日常保持胜过任何临时优化。",
        "日常习惯",
    )

    # 排序：按时间 + 维度稳定顺序
    period_rank = {"立即": 0, "1-3 个月": 1, "3-6 个月": 2, "6 个月+": 3, "持续": 4}
    source_rank = {
        "征信修复": 0,
        "收入证明": 1,
        "资产配置": 2,
        "申请策略": 3,
        "日常习惯": 4,
    }
    suggestions.sort(
        key=lambda x: (period_rank.get(x["period"], 9), source_rank.get(x["source"], 9))
    )

    # 「持续 / 日常习惯」类建议作为兜底（永远保留），其余按时间排序封顶到 7 条
    ongoing = [s for s in suggestions if s["period"] == "持续"]
    urgent = [s for s in suggestions if s["period"] != "持续"]
    return (urgent[:7] + ongoing)[:8]


# ============================================================================
# 银行关注维度识别
# ============================================================================


_BANK_FOCUS_MAP: list[tuple[str, list[str]]] = [
    # (label, keywords) — 关键词尽量精确，避免「额度/客户」等通用词误判
    ("公积金",         ["公积金", "公积金专项"]),
    ("代发工资",       ["代发工资", "代发"]),
    ("房产",           ["房产", "抵押", "房贷", "房抵"]),
    ("小微/电商流水",  ["小微", "电商", "流水贷", "卖家"]),
    ("存量客户",       ["已有客户", "存量", "老客户", "VIP", "白金卡"]),
    ("审批快",         ["闪电贷", "快贷", "审批快", "快速", "3 分钟", "线上申请", "纯线上"]),
    ("高额度",         ["额度上限高", "高额度", "上限高", "额度高"]),
    ("保险",           ["保险客户", "保单"]),
    ("外汇",           ["外汇", "境外", "外贸", "海外"]),
]


def _bank_focus_keywords(features: list[str]) -> list[str]:
    """从银行 features 列表里抽取该行的关注维度（最多 3 个，去重保序）"""
    if not features:
        return []
    text = " ".join(features)
    out: list[str] = []
    for label, kws in _BANK_FOCUS_MAP:
        if any(k in text for k in kws):
            out.append(label)
        if len(out) >= 3:
            break
    return out


def _focus_to_phrase(focus_kw: list[str]) -> str:
    """把维度列表转成自然语言短语，用于理由段中的「该行偏好」挂载"""
    if not focus_kw:
        return ""
    if len(focus_kw) == 1:
        return focus_kw[0]
    if len(focus_kw) == 2:
        return f"{focus_kw[0]}、{focus_kw[1]}"
    return "、「.join(focus_kw[:-1]) + f」、{focus_kw[-1]}"


# ============================================================================
# 5 大维度评分汇总
# ============================================================================


# 固定 5 大类（DB 里的 category 字段）
_CATEGORY_ORDER: list[str] = ["基础", "职业", "收入", "资产", "征信"]
_CATEGORY_LABELS: dict[str, str] = {
    "基础": "基础信息",
    "职业": "职业背景",
    "收入": "收入水平",
    "资产": "资产配置",
    "征信": "征信记录",
}
# 各维度"满分"经验值（用于归一化到 0-100）
# 按 DB 通用规则里每个 category 的正分最大值之和估算
_CATEGORY_MAX: dict[str, float] = {
    "基础": 30.0,   # 年龄(10) + 学历(4) + 婚姻(2) + ...
    "职业": 28.0,   # 单位(8) + 工龄(8) + 城市(6) + ...
    "收入": 30.0,   # 月收入(10) + 代发(3) + 社保(3) + ...
    "资产": 30.0,   # 房(8) + 车(3) + 存款(3) + ...
    "征信": 30.0,   # 信用卡(6) + 查询(6) + 逾期(6) + 笔数(4) + ...
}


def _aggregate_category_scores(
    product_results: list | None,
    category_max: dict[str, float] | None = None,
) -> dict[str, dict]:
    """
    把 6 套产品的 matched_items 按 category 维度汇总，得出用户在 5 大类下的相对得分。

    策略：
      1. 选 recommend=True 的产品作为"主参考"（与 synthesize_overall_score 的加权逻辑对齐）
      2. 兜底：选 score 最高的产品
      3. 都没有：所有产品平均

    返回: {
        "基础": {"raw": 12.0, "max": 16.0, "ratio": 75.0, "level": "strong", "low": false, "items": 3},
        ...
      }
      - level: strong(>=70) / mid(40-69) / weak(<40)
      - low: 是否需要重点改善

    category_max：可选，传入「每类目理论满分」用于归一化。None 时用内置经验值。
    """
    results = product_results or []
    max_map = category_max or _CATEGORY_MAX

    if not results:
        return _empty_category_scores(max_map)

    # 1. 选 recommend 产品
    picked = next((r for r in results if r.get("recommend")), None)
    # 2. 兜底：选 score 最高
    if not picked:
        picked = max(results, key=lambda r: r.get("score", 0))
    # 3. 兜底兜底：所有产品求平均
    items_source: list[dict] = []
    if picked:
        items_source = picked.get("matched_items") or []
    if not items_source:
        for r in results:
            for it in r.get("matched_items") or []:
                items_source.append(it)

    buckets: dict[str, list[float]] = {cat: [] for cat in _CATEGORY_ORDER}
    for it in items_source:
        cat = it.get("category")
        sc = float(it.get("score", 0))
        if not cat or cat not in buckets:
            continue
        # 只累计正分（命中贡献），负分不扣（扣分由其他规则体现）
        if sc > 0:
            buckets[cat].append(sc)

    out: dict[str, dict] = {}
    for cat in _CATEGORY_ORDER:
        scores = buckets.get(cat) or []
        raw = round(sum(scores), 1)
        max_v = float(max_map.get(cat, 20.0))
        ratio = round(min(100.0, (raw / max_v) * 100.0), 1) if max_v > 0 else 0.0
        if ratio >= 70:
            level = "strong"
        elif ratio >= 40:
            level = "mid"
        else:
            level = "weak"
        out[cat] = {
            "label": _CATEGORY_LABELS.get(cat, cat),
            "raw": raw,
            "max": max_v,
            "ratio": ratio,
            "level": level,
            "low": level == "weak",
            "items": len(scores),
        }
    return out


def _empty_category_scores() -> dict[str, dict]:
    return {
        cat: {
            "label": _CATEGORY_LABELS.get(cat, cat),
            "raw": 0.0,
            "max": _CATEGORY_MAX.get(cat, 20.0),
            "ratio": 0.0,
            "level": "weak",
            "low": True,
            "items": 0,
        }
        for cat in _CATEGORY_ORDER
    }


# 维度对应的「为什么需要改善」一句话解释（前端提示用）
_CATEGORY_LOW_HINT: dict[str, str] = {
    "基础": "年龄 / 学历 / 婚姻等基础信息对该行模型有影响",
    "职业": "单位性质 / 工作年限 / 城市层级属于稳定性指标",
    "收入": "月收入 / 代发 / 社保决定该行愿意给的额度上限",
    "资产": "房产 / 车产 / 存款是该行模型中常用的担保或加分项",
    "征信": "逾期 / 查询 / 在贷笔数是该行准入与定价的硬指标",
}


# ============================================================================
# 查免费结果
# ============================================================================


@router.get("/free/{assessment_id}", summary="获取免费结果详情（6 产品摘要）")
async def get_free_result(
    assessment_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
) -> dict:
    a = await db.get(Assessment, assessment_id)
    if not a:
        raise NotFoundException(f"测评记录 {assessment_id} 不存在")

    return ok({
        "assessment_id": a.id,
        "report_no": a.report_no,
        "overall": {
            "score": a.score,
            "level": a.level,
            "limit_min": a.limit_min,
            "limit_max": a.limit_max,
            "rate_min": float(a.rate_min) if a.rate_min is not None else 0,
            "rate_max": float(a.rate_max) if a.rate_max is not None else 0,
            "pass_probability": a.pass_probability,
        },
        "free_summary": _build_free_summary_from_db(a),
        "product_results": a.product_results or [],   # 6 个产品摘要
        # v3.2 新增：免费版只露 1 个核心问题（其余在 pay.vue 模糊）
        "top_issue_free": (a.top_issues or [None])[0] if a.top_issues else None,
        "top_issues_total": len(a.top_issues or []),
        "improvement_projection": a.improvement_projection or None,
        "one_sentence": _build_one_sentence(
            a.level or "E", a.top_issues or [], a.improvement_projection or None
        ),
        "is_paid": bool(a.is_paid),
        "created_at": a.created_at.isoformat() if a.created_at else None,
    })


def _build_free_summary_from_db(a: Assessment) -> str:
    if not a.score:
        return ""
    limit_lo = (a.limit_min or 0) // 10000
    limit_hi = (a.limit_max or 0) // 10000
    if a.level in ("S", "A", "B"):
        return f"您是 {a.level} 级客户，模拟可获额度 {limit_lo}-{limit_hi} 万元，通过率 {a.pass_probability}。"
    if a.level == "C":
        return f"您是 {a.level} 级客户，模拟可获额度 {limit_lo}-{limit_hi} 万元，建议优化后再申请。"
    return f"当前评级 {a.level}，建议先改善条件再申请。"


# ============================================================================
# 查完整报告（付费后）
# ============================================================================


@router.get("/report/{assessment_id}", summary="获取完整报告（6 产品详情 + 改善建议）")
async def get_full_report(
    assessment_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
) -> dict:
    a = await db.get(Assessment, assessment_id)
    if not a:
        raise NotFoundException(f"测评记录 {assessment_id} 不存在")

    # 未付费：返回分级内容（6 个产品中只显示前 1 个完整 + 5 个模糊）
    if not a.is_paid:
        # 改造建议：返回前 1 条 + 模糊 2 条，刺激解锁
        all_sugs = a.suggestions or []
        sug_visible = all_sugs[:1]
        sug_blur = all_sugs[1:3]
        return ok({
            "report_no": a.report_no,
            "is_paid": False,
            "message": "请先解锁完整报告（9.99 元）",
            "overall": {
                "score": a.score,
                "level": a.level,
                "limit_min": a.limit_min,
                "limit_max": a.limit_max,
                "rate_min": float(a.rate_min) if a.rate_min else 0,
                "rate_max": float(a.rate_max) if a.rate_max else 0,
                "pass_probability": a.pass_probability,
            },
            "category_scores": _aggregate_category_scores(a.product_results),
            "product_results_preview": (a.product_results or [])[:1],  # 只看 1 个
            "product_results_locked": (a.product_results or [])[1:],  # 5 个模糊
            # 改造建议：付费页用 1 可见 + 2 模糊
            "suggestions_preview": sug_visible,
            "suggestions_locked_count": len(sug_blur),
            "suggestions_total_count": len(all_sugs),
        })

    # 已付费：返回完整 6 个产品详情 + 改善建议
    return ok({
        "report_no": a.report_no,
        "is_paid": True,
        "paid_at": a.paid_at.isoformat() if a.paid_at else None,
        "overall": {
            "score": a.score,
            "level": a.level,
            "limit_min": a.limit_min,
            "limit_max": a.limit_max,
            "rate_min": float(a.rate_min) if a.rate_min else 0,
            "rate_max": float(a.rate_max) if a.rate_max else 0,
            "pass_probability": a.pass_probability,
        },
        "category_scores": _aggregate_category_scores(a.product_results),
        "product_results": a.product_results or [],   # 6 个完整
        "advantages": a.advantages or [],
        "weak_points": a.weak_points or [],
        "risk_tags": a.risk_tags or [],
        "suggestions": a.suggestions or [],
        # v3.2 新增：核心问题 + 改善推演（7 大模块报告的数据源）
        "top_issues": a.top_issues or [],
        "improvement_projection": a.improvement_projection or None,
        "one_sentence": _build_one_sentence(
            a.level or "E", a.top_issues or [], a.improvement_projection or None,
            a.pass_probability or "",
        ),
        "apply_strategy": _build_apply_strategy(a),
        "disclaimer": (
            "本报告由信测通模拟评审模型生成。"
            "模型逻辑参考银行信用贷审批框架（A 卡 / B 卡 / 反欺诈层），"
            "额度、利率、综合通过率按真实业务区间测算，"
            "但本平台不查征信、不接入任何银行系统、不收集您的真实数据。"
            "本报告基于您主动填写的信息进行模拟分析，"
            "所有评分、额度、利率、通过概率均为模拟计算结果，"
            "不代表任何银行或金融机构的真实授信，"
            "不构成贷款承诺、投资建议或法律意见。"
            "本报告中的额度已按银保监 2020/7《关于加强商业银行互联网贷款业务管理》"
            "及商业银行自营消费贷行业惯例限高：互联网消费贷单户 ≤ 30 万，"
            "线下消费贷单户 ≤ 100 万，公积金贷单户 ≤ 120 万，"
            "小微企业税贷/开票贷 ≤ 500 万，房抵贷 ≤ 1000 万。"
        ),
    })


def _build_apply_strategy(a: Assessment) -> str:
    if a.level in ("S", "A"):
        return "建议同时申请 2-3 家银行（如建行快贷、招行闪电贷、平安新一贷），择优放款。优先公积金 / 工资代发行。"
    if a.level == "B":
        return "建议先申请 1-2 家银行（如工行融e借、招行闪电贷），通过率较高后再尝试其他。"
    if a.level == "C":
        return "建议先申请 1 家通过率中等的银行（如商业银行消金产品），通过后再尝试额度提升。"
    return "建议暂缓申请，先改善征信 / 收入后再来。"
