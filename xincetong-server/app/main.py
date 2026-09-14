"""
信测通后端服务 - FastAPI 入口
信用贷模拟评审工具（不查征信、不碰真实放贷）

v3.3 升级（2026-09-10）：兼容 Vercel Serverless
  - 禁用 lifespan（Vercel 不会调 startup/shutdown）
  - 禁用 Redis（Vercel 无长连接进程）
  - module 顶层 init_db()（serverless 冷启动时一次性初始化）
"""
import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assessment
from app.api import bank as bank_api
from app.api import legal
from app.api import order
from app.api import product
from app.api import site
from app.api import track
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.database import init_db
from app.utils.logger import logger
from app.utils.response import ok


# ============================================================================
# 顶层初始化（Vercel 兼容）
#   - lifespan 在 Vercel 上不会被调用
#   - 改为 module import 时执行（每次冷启动时跑一次）
# ============================================================================
if os.environ.get("INIT_RUNTIME") != "1":
    os.environ["INIT_RUNTIME"] = "1"
    try:
        asyncio.get_event_loop().run_until_complete(init_db())
        logger.info(f"信测通后端启动 v3.3 (env={settings.ENV}, db={settings.mysql_dsn.split('@')[-1].split('?')[0]})")
    except RuntimeError:
        # Vercel 上没 event loop，延后到第一次请求时再初始化
        logger.warning("无 event loop，DB 初始化延后到首次请求")
    except Exception as e:
        logger.error(f"顶层 DB 初始化失败（将由首次请求重试）: {e}")


app = FastAPI(
    title="信测通 API",
    description="信用贷模拟评审工具（模拟结果，非银行官方，不查征信）",
    version="0.3.4",
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url=None,
)

# Vercel serverless：首次请求兜底再 init 一次
_db_ready = {"ok": False}


@app.middleware("http")
async def ensure_db_ready(request, call_next):
    """首次请求时若顶层初始化失败，再补一次 init_db"""
    if not _db_ready["ok"]:
        try:
            await init_db()
            _db_ready["ok"] = True
        except Exception as e:
            logger.error(f"首请求 DB 初始化失败: {e}")
    return await call_next(request)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
register_exception_handlers(app)


# ============================================================================
# 健康检查
# ============================================================================


@app.get("/", tags=["健康检查"])
async def root():
    return ok({
        "app": "xincetong",
        "version": "0.3.4",
        "env": settings.ENV,
        "stage": "v3.4 报告逻辑优化",
        "disclaimer": "模拟测评 · 非银行官方 · 不查征信",
    })


@app.get("/health", tags=["健康检查"])
async def health():
    return ok({"status": "ok"})


# ============================================================================
# 路由注册
# ============================================================================


# 测评（v3: 6 大产品独立）
app.include_router(assessment.router, prefix="/api/assessment", tags=["测评"])

# 站点配置（数字+文案+合规变量化）
app.include_router(site.router, prefix="/api/site", tags=["站点配置"])

# 6 大产品类型
app.include_router(product.router, prefix="/api/product-types", tags=["产品类型"])

# 银行（保留兼容，作为方法论/推广素材）
app.include_router(bank_api.router, prefix="/api/banks", tags=["银行"])

# 订单 / 支付（v3: 9.99 解锁）
app.include_router(order.router, prefix="/api/order", tags=["订单支付"])

# 埋点（H5/小程序/App 共用，前端调 /api/track 上报）
app.include_router(track.router, prefix="/api/track", tags=["埋点"])

# 法务 AI 咨询（DeepSeek）
app.include_router(legal.router, prefix="/api/legal", tags=["法务咨询"])

# 阶段 3-6 启用：
# app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
# app.include_router(promoter.router, prefix="/api/promoter", tags=["推广员"])
# app.include_router(share.router, prefix="/api/share", tags=["分享"])
# app.include_router(admin.router, prefix="/api/admin", tags=["管理后台"])
# app.include_router(report.router, prefix="/api/report", tags=["报告"])
