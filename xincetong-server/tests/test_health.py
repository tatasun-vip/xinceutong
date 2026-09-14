"""
健康检查测试：验证 FastAPI 启动后根路径 + /health 返回统一 {code, message, data} 格式
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/")
    assert r.status_code == 200
    body = r.json()
    # 统一响应格式
    assert body["code"] == 0
    assert body["message"] == "success"
    assert "data" in body
    assert body["data"]["app"] == "xincetong"
    assert "disclaimer" in body["data"]


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "ok"
