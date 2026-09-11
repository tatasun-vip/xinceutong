"""
管理后台路由（占位）
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/scorecard", summary="配置评分卡")
async def update_scorecard():
    return {"code": 0, "message": "TODO", "data": None}


@router.post("/validation", summary="配置纠错规则")
async def update_validation():
    return {"code": 0, "message": "TODO", "data": None}


@router.get("/promoters", summary="推广员审核列表")
async def list_promoters():
    return {"code": 0, "message": "TODO", "data": None}


@router.post("/promoter/approve", summary="审核通过/拒绝")
async def approve_promoter():
    return {"code": 0, "message": "TODO", "data": None}


@router.get("/stats", summary="平台数据看板")
async def get_stats():
    return {"code": 0, "message": "TODO", "data": None}
