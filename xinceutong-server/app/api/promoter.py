"""
推广员路由（占位）
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/apply", summary="申请入驻")
async def apply_promoter():
    return {"code": 0, "message": "TODO", "data": None}


@router.get("/dashboard", summary="工作台数据")
async def get_dashboard():
    return {"code": 0, "message": "TODO", "data": None}


@router.get("/tools", summary="获取推广链接/二维码")
async def get_tools():
    return {"code": 0, "message": "TODO", "data": None}


@router.post("/price", summary="设置专属价格")
async def set_price():
    return {"code": 0, "message": "TODO", "data": None}


@router.get("/customers", summary="客户列表")
async def get_customers():
    return {"code": 0, "message": "TODO", "data": None}


@router.get("/customer/{customer_id}", summary="客户详情")
async def get_customer_detail(customer_id: int):
    return {"code": 0, "message": "TODO", "data": None}


@router.get("/commissions", summary="分佣明细")
async def get_commissions():
    return {"code": 0, "message": "TODO", "data": None}


@router.post("/withdraw", summary="申请提现")
async def apply_withdraw():
    return {"code": 0, "message": "TODO", "data": None}
