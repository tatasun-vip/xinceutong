"""
自定义业务异常 + FastAPI 全局异常处理器
统一返回 {code, message, data} 格式
"""
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.utils.logger import logger


class BizException(Exception):
    """业务异常基类"""

    code: int = 1
    message: str = "业务异常"
    http_status: int = status.HTTP_400_BAD_REQUEST

    def __init__(
        self,
        message: str | None = None,
        code: int | None = None,
        http_status: int | None = None,
    ):
        self.message = message or self.message
        if code is not None:
            self.code = code
        if http_status is not None:
            self.http_status = http_status
        super().__init__(self.message)


class NotFoundException(BizException):
    code = 404
    message = "资源不存在"
    http_status = status.HTTP_404_NOT_FOUND


class AuthException(BizException):
    code = 401
    message = "未登录或登录已过期"
    http_status = status.HTTP_401_UNAUTHORIZED


class PermissionDeniedException(BizException):
    code = 403
    message = "权限不足"
    http_status = status.HTTP_403_FORBIDDEN


class ParamException(BizException):
    code = 400
    message = "参数错误"
    http_status = status.HTTP_400_BAD_REQUEST


class PayException(BizException):
    code = 402
    message = "支付异常"
    http_status = status.HTTP_402_PAYMENT_REQUIRED


class RateLimitException(BizException):
    code = 429
    message = "请求过于频繁"
    http_status = status.HTTP_429_TOO_MANY_REQUESTS


def _wrap(code: int, message: str, data=None) -> dict:
    """统一响应包装"""
    return {"code": code, "message": message, "data": data}


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器，所有响应都走 {code, message, data} 格式"""

    @app.exception_handler(BizException)
    async def biz_handler(_: Request, exc: BizException):
        return JSONResponse(
            status_code=exc.http_status,
            content=_wrap(exc.code, exc.message),
        )

    @app.exception_handler(HTTPException)
    async def http_handler(_: Request, exc: HTTPException):
        # FastAPI 自带的 HTTPException（如 405/500）也包成统一格式
        return JSONResponse(
            status_code=exc.status_code,
            content=_wrap(exc.status_code, str(exc.detail) or "请求失败"),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        # Pydantic 参数校验失败
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(x) for x in first.get("loc", []))
        msg = first.get("msg", "参数错误")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_wrap(422, f"{loc} {msg}" if loc else msg),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception):
        # 兜底：所有未捕获异常
        logger.exception(f"未捕获异常: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_wrap(500, "服务异常，请稍后再试"),
        )
