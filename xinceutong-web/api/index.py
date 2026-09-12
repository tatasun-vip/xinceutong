"""
Vercel Serverless 入口（Python ASGI）
转发所有请求到 FastAPI app

Vercel Python runtime 会把仓库根加入 sys.path，
但我们用了 monorepo 结构，需要手动加 xinceutong-server 进去
"""
import os
import sys

# 把后端项目根加入 sys.path，让 from app.xxx import yyy 能找到
_BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "xinceutong-server")
sys.path.insert(0, os.path.abspath(_BACKEND_ROOT))

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
