"""
报告生成服务（阶段 2 基础版 / 阶段 4 增强）

阶段 2 负责：
- 从 DB 读取 Assessment
- 整合评分卡结果 + 风险标签 + 建议 + 产品对比
- 输出完整报告

阶段 4 增强：
- 整合多产品对比（人工标注 + 模拟数据）
- 生成报告 PDF / 海报图
- 改善建议时间表
"""
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment
from app.core.exceptions import NotFoundException


def build_full_report(assessment: Assessment) -> dict[str, Any]:
    """组装完整报告"""
    return {
        "report_no": assessment.report_no,
        "score": assessment.score,
        "level": assessment.level,
        "limit_min": assessment.limit_min,
        "limit_max": assessment.limit_max,
        "rate_min": float(assessment.rate_min) if assessment.rate_min else 0,
        "rate_max": float(assessment.rate_max) if assessment.rate_max else 0,
        "pass_probability": assessment.pass_probability,
        "risk_tags": assessment.risk_tags or [],
        "advantages": assessment.advantages or [],
        "weak_points": assessment.weak_points or [],
        "suggestions": assessment.suggestions or [],
        "products": assessment.products or [],
        "apply_strategy": _build_apply_strategy(assessment),
        "disclaimer": "本报告为模拟结果，不查征信、不构成贷款承诺。实际审批以金融机构为准。",
    }


def _build_apply_strategy(a: Assessment) -> str:
    if a.level in ("S", "A"):
        return "建议同时申请 2-3 家银行（如建行快贷、招行闪电贷、平安新一贷），择优放款。优先公积金 / 工资代发行。"
    if a.level == "B":
        return "建议先申请 1-2 家银行（如工行融e借、招行闪电贷），通过率较高后再尝试其他。"
    if a.level == "C":
        return "建议先申请 1 家通过率中等的银行（如商业银行消金产品），通过后再尝试额度提升。"
    return "建议暂缓申请，先改善征信 / 收入后再来。"


async def get_report_by_id(assessment_id: int, db: AsyncSession) -> dict:
    """从 DB 加载并组装报告"""
    a = await db.get(Assessment, assessment_id)
    if not a:
        raise NotFoundException(f"测评记录 {assessment_id} 不存在")
    return build_full_report(a)
