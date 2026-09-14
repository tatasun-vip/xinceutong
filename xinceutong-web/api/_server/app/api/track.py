"""
api/track.py - 埋点事件接收

接收前端 /api/track 上报，存到 DB（可选），目前只打日志。
H5/小程序/App 都会调，schema 兼容。
"""
import json
from typing import Any, Dict

from fastapi import APIRouter, Request

from app.utils.logger import logger

router = APIRouter()


@router.post("")
async def track_event(request: Request) -> Dict[str, Any]:
    """埋点接收：开发期只 log，生产期可扩展写 DB / 发到分析平台"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    event = body.get("event", "unknown")
    page = body.get("page", "-")
    platform = body.get("platform", "-")

    logger.info(f"[track] platform={platform} event={event} page={page} data={json.dumps(body.get('data') or {}, ensure_ascii=False)}")

    return {"ok": True}
