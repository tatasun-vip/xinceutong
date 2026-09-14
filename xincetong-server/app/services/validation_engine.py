"""
实时纠错校验引擎

读取 validation_rules 表，对当前填写数据做实时校验。
返回 [{rule_name, level, message, condition}, ...]

按 level 排序：error > warning > info
"""
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scorecard import ValidationRule
from app.utils.condition_dsl import evaluate
from app.utils.logger import logger


async def _load_rules(db: AsyncSession, enabled_only: bool = True) -> list[ValidationRule]:
    stmt = select(ValidationRule)
    if enabled_only:
        stmt = stmt.where(ValidationRule.enabled == 1)
    res = await db.execute(stmt)
    return list(res.scalars().all())


def _level_rank(level: str) -> int:
    return {"error": 3, "warning": 2, "info": 1}.get(level, 0)


async def validate_input(
    input_data: dict,
    type_: str = "personal",
    db: AsyncSession | None = None,
) -> list[dict[str, Any]]:
    """
    实时校验：
    - 遍历 validation_rules，evaluate condition_json
    - 命中的规则返回其消息
    - 排序：error > warning > info
    """
    if db is None:
        # 调试模式无 DB 时返回空
        return []

    try:
        rules = await _load_rules(db)
    except Exception as e:
        logger.error(f"validation: 加载规则失败 {e}")
        return []

    hits: list[dict[str, Any]] = []
    for r in rules:
        try:
            cond = r.condition_json if isinstance(r.condition_json, dict) else {}
            if evaluate(cond, input_data):
                hits.append(
                    {
                        "rule_name": r.rule_name,
                        "level": r.level,
                        "message": r.message,
                    }
                )
        except Exception as e:
            # 单条规则评估失败不阻塞其他
            logger.warning(f"validation: 规则 {r.rule_name} 评估失败: {e}")

    hits.sort(key=lambda x: _level_rank(x["level"]), reverse=True)
    return hits
