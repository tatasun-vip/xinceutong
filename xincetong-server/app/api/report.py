"""
完整报告路由（占位）
GET /api/assessment/report/{id}
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/report/{assessment_id}", summary="获取完整报告（需付费）")
async def get_full_report(assessment_id: int):
    return {"code": 0, "message": "TODO", "data": None}
