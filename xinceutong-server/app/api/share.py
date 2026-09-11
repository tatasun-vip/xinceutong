"""
分享路由（占位）
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/generate", summary="生成分享码/海报")
async def generate_share():
    return {"code": 0, "message": "TODO", "data": None}


@router.get("/check/{code}", summary="校验分享码")
async def check_share_code(code: str):
    return {"code": 0, "message": "TODO", "data": None}
