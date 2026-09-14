"""
字典辅助工具
"""
from typing import Any


def get_path(data: dict, path: str, default: Any = None) -> Any:
    """支持 'a.b.c' 点路径取嵌套字段"""
    cur: Any = data
    for key in path.split("."):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return default
    return cur
