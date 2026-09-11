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
from app.main import app  # noqa: E402
