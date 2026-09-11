"""
统一响应格式：{code, message, data}
code=0 成功；code!=0 失败，message 为错误提示
"""
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应"""

    code: int = Field(..., description="0=成功，其他=失败")
    message: str = Field(..., description="提示信息")
    data: Optional[T] = Field(default=None, description="业务数据")


def ok(data: Any = None, message: str = "success") -> dict:
    """成功响应"""
    return {"code": 0, "message": message, "data": data}


def fail(message: str = "fail", code: int = 1, data: Any = None) -> dict:
    """失败响应（业务异常用 BizException；这里给路由直接返回用）"""
    return {"code": code, "message": message, "data": data}
