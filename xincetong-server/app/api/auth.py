"""
认证相关路由（占位，业务阶段实现）
POST /api/auth/wechat-login
GET  /api/auth/profile
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/wechat-login", summary="微信登录")
async def wechat_login():
    """用 code 换 openid，签发 JWT"""
    return {"code": 0, "message": "TODO", "data": None}


@router.get("/profile", summary="获取当前用户信息")
async def profile():
    return {"code": 0, "message": "TODO", "data": None}


@router.post("/grant", summary="用户授权推广员查看报告")
async def grant_to_promoter():
    return {"code": 0, "message": "TODO", "data": None}


@router.get("/grant-status", summary="查询授权状态")
async def grant_status():
    return {"code": 0, "message": "TODO", "data": None}
