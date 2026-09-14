"""
api/legal.py - 法务 AI 咨询接口

POST /api/legal/chat    - 发送问题获取 AI 回答
GET  /api/legal/usage   - 查询免费次数（前端展示用）
GET  /api/legal/scenarios - 获取常见场景列表（前端快速入口）

MVP 简化：
- 不做严格 quota 验证（Vercel 无数据库）
- 依赖前端 localStorage 记录免费次数
- 不保存聊天历史（MVP 阶段）
"""
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.legal_ai import get_legal_ai
from app.services.legal_prompt import SCENARIO_PROMPTS, SCENARIO_TITLES, SYSTEM_PROMPT
from app.utils.logger import logger


router = APIRouter()


# ============ Schemas ============


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1, max_length=20)
    user_id: Optional[str] = None  # MVP 不用，仅记录
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    usage: Dict[str, int]
    model: str
    latency_ms: int


class UsageResponse(BaseModel):
    enabled: bool
    free_limit: int
    message: str


class Scenario(BaseModel):
    key: str
    title: str
    prompt: str


# ============ Endpoints ============

FREE_LIMIT = 1  # 1 次免费


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    发送法务咨询问题，调用 DeepSeek 返回 AI 回答

    MVP 行为：
    - 不做严格 quota 验证（前端 localStorage 控）
    - 不存历史（每次会话独立）
    - 但每次调用都做日志 + 错误处理
    """
    ai = get_legal_ai()

    if not ai.enabled:
        raise HTTPException(
            status_code=503,
            detail={
                "code": 503,
                "message": "法务 AI 暂未配置 DEEPSEEK_API_KEY，请联系管理员",
            },
        )

    # 转换消息格式
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]

    t0 = time.time()
    try:
        result = await ai.chat(
            messages=msgs,
            system=SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=1200,
        )
    except RuntimeError as e:
        logger.error(f"法务 AI 调用失败: {e}")
        raise HTTPException(
            status_code=502,
            detail={"code": 502, "message": str(e)},
        )
    except Exception as e:
        logger.exception(f"法务 AI 未知错误: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": 500, "message": "服务异常，请稍后重试"},
        )

    latency_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[legal] session={req.session_id} user={req.user_id} "
        f"latency={latency_ms}ms tokens={result['usage']['total_tokens']}"
    )

    return ChatResponse(
        reply=result["content"],
        usage=result["usage"],
        model=result["model"],
        latency_ms=latency_ms,
    )


@router.get("/usage", response_model=UsageResponse)
async def usage() -> UsageResponse:
    """返回当前是否启用 + 免费次数（前端用）"""
    ai = get_legal_ai()
    return UsageResponse(
        enabled=ai.enabled,
        free_limit=FREE_LIMIT,
        message="已启用" if ai.enabled else "暂未配置 DeepSeek API key",
    )


@router.get("/scenarios", response_model=List[Scenario])
async def scenarios() -> List[Scenario]:
    """返回常见场景列表（前端快速入口用）"""
    return [
        Scenario(key=k, title=SCENARIO_TITLES[k], prompt=v)
        for k, v in SCENARIO_PROMPTS.items()
    ]
