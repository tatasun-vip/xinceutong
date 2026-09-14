"""
Vercel Serverless 入口（Python ASGI）
转发所有请求到 FastAPI app

Vercel Python runtime 只把 api/ 目录的文件传到 function runtime，
所以我们把 xinceutong-server/ 复制到 api/_server/ 一并打包。
"""
import os
import sys

# 后端项目根：api/_server
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "_server"))
sys.path.insert(0, _BACKEND_ROOT)

# 导入 FastAPI app（顶层会触发 init_db）
from app.main import app as _fastapi_app  # noqa: E402


class _ApiCompatMiddleware:
    """把 /api/health 和 /api/ 重写到 /health 和 /

    - 业务路由（/api/assessment/...）保持原样，main.py 已经加了 /api 前缀
    - 只对 /api/health 和 /api/ 这两个根级路径做兼容
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            if path == "/api/health" or path == "/api/":
                scope["path"] = path[4:] or "/"
        return await self.app(scope, receive, send)


app = _ApiCompatMiddleware(_fastapi_app)
