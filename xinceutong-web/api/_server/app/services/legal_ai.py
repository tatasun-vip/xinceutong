"""
services/legal_ai.py - 法务 AI 客服（DeepSeek）

为信测通用户提供贷款逾期、信用卡、征信等法律问题的智能咨询。
"""
import json
import os
from typing import Any, Dict, List, Optional

import httpx

from app.utils.logger import logger


class LegalAI:
    """DeepSeek API 客户端（兼容 OpenAI 协议）"""

    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL", self.DEFAULT_BASE_URL)
        self.model = model or os.environ.get("DEEPSEEK_MODEL", self.DEFAULT_MODEL)
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> Dict[str, Any]:
        """
        调用 DeepSeek 聊天补全 API

        Args:
            messages: OpenAI 格式消息列表 [{"role": "user", "content": "..."}, ...]
            system: 系统提示词
            temperature: 随机性 0-1
            max_tokens: 最大输出 tokens

        Returns:
            {"content": str, "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}}
        """
        if not self.enabled:
            raise RuntimeError("DEEPSEEK_API_KEY 未配置")

        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )

            if r.status_code != 200:
                logger.error(f"DeepSeek API 错误 {r.status_code}: {r.text[:500]}")
                raise RuntimeError(f"AI 服务异常 ({r.status_code})")

            data = r.json()
            choice = data["choices"][0]
            content = choice["message"]["content"]
            usage = data.get("usage", {})

            return {
                "content": content,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                "model": self.model,
            }


# 单例（懒加载）
_ai_instance: Optional[LegalAI] = None


def get_legal_ai() -> LegalAI:
    """获取法务 AI 单例"""
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = LegalAI()
    return _ai_instance
