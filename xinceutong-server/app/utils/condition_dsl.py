"""
纠错规则 DSL 评估器

condition_json 支持的操作符：
  - 比较: eq / ne / in / not_in / gte / lte / gt / lt / contains
  - 组合: and / or / not
  - 路径: variable 支持 'a.b.c' 点路径

示例:
  {"op": "eq", "variable": "current_overdue", "value": "有"}
  {"op": "in", "variable": "monthly_income", "value": ["5000以下", "5000-8000"]}
  {"op": "and", "children": [
      {"op": "gte", "variable": "credit_card_usage", "value": "80%以上"},
      {"op": "eq", "variable": "current_overdue", "value": "无"}
  ]}
"""
from typing import Any

from app.utils.dict_helper import get_path


def _get(data: dict, variable: str) -> Any:
    """支持点路径取嵌套字段"""
    return get_path(data, variable)


def _eq(data: dict, cond: dict) -> bool:
    return _get(data, cond["variable"]) == cond["value"]


def _ne(data: dict, cond: dict) -> bool:
    return _get(data, cond["variable"]) != cond["value"]


def _in(data: dict, cond: dict) -> bool:
    val = _get(data, cond["variable"])
    if val is None:
        return False
    target = cond["value"]
    return val in (target if isinstance(target, list) else [target])


def _not_in(data: dict, cond: dict) -> bool:
    return not _in(data, cond)


def _gte(data: dict, cond: dict) -> bool:
    val = _get(data, cond["variable"])
    return val is not None and val >= cond["value"]


def _lte(data: dict, cond: dict) -> bool:
    val = _get(data, cond["variable"])
    return val is not None and val <= cond["value"]


def _gt(data: dict, cond: dict) -> bool:
    val = _get(data, cond["variable"])
    return val is not None and val > cond["value"]


def _lt(data: dict, cond: dict) -> bool:
    val = _get(data, cond["variable"])
    return val is not None and val < cond["value"]


def _contains(data: dict, cond: dict) -> bool:
    val = _get(data, cond["variable"])
    if isinstance(val, (list, tuple, set)):
        return cond["value"] in val
    if isinstance(val, str):
        return cond["value"] in val
    return False


_OPS = {
    "eq": _eq,
    "ne": _ne,
    "in": _in,
    "not_in": _not_in,
    "gte": _gte,
    "lte": _lte,
    "gt": _gt,
    "lt": _lt,
    "contains": _contains,
}


def evaluate(condition: dict, data: dict) -> bool:
    """
    评估 condition 是否对 data 成立
    :param condition: 条件字典
    :param data: 用户填写数据
    """
    op = condition.get("op")
    if op in ("and", "or"):
        children = condition.get("children", [])
        if op == "and":
            return all(evaluate(c, data) for c in children)
        return any(evaluate(c, data) for c in children)
    if op == "not":
        return not evaluate(condition["child"], data)
    if op in _OPS:
        return _OPS[op](data, condition)
    # 未知操作符默认不命中（保守）
    return False
