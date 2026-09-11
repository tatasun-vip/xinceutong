"""
订单 / 支付 路由（v3 完整实现 + mock 支付）

POST /api/order/create        创建订单（9.99 元）
POST /api/order/mock-pay/{order_no}  模拟支付（点解锁按钮直接调用）
GET  /api/order/status/{order_no}    查订单状态
"""
import asyncio
from decimal import Decimal

from fastapi import APIRouter, Depends, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_optional
from app.core.exceptions import NotFoundException, ParamException
from app.database import get_db
from app.models.assessment import Assessment
from app.models.order import Order
from app.models.user import User
from app.utils.id_generator import gen_order_no
from app.utils.logger import logger
from app.utils.response import ok

router = APIRouter()

# 解锁价格（元）— v3 改 9.99，从 site_config 读（写死兜底）
UNLOCK_PRICE = Decimal("9.99")


@router.post("/create", summary="创建订单（9.99 元解锁完整报告）")
async def create_order(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict:
    """
    body: { assessment_id, promoter_code? }
    返回：{ order_no, amount, status, qrcode? }
    """
    assessment_id = body.get("assessment_id")
    if not assessment_id:
        raise ParamException("assessment_id 不能为空")

    a = await db.get(Assessment, assessment_id)
    if not a:
        raise NotFoundException(f"测评记录 {assessment_id} 不存在")
    if a.is_paid:
        raise ParamException("该报告已解锁，无需重复支付")

    user_id = current_user.id if current_user else 0

    # 解析推广码（如有）
    promoter_id = None
    promoter_code = body.get("promoter_code")
    if promoter_code:
        from app.models.promoter import Promoter, PromoterLink
        link_row = await db.execute(select(PromoterLink).where(PromoterLink.code == promoter_code))
        link = link_row.scalar_one_or_none()
        if link:
            promoter_id = link.promoter_id
            logger.info(f"order from promoter_id={promoter_id} code={promoter_code}")

    # 查推广员自定义价格
    amount = UNLOCK_PRICE
    base_price = UNLOCK_PRICE
    markup = Decimal("0")
    if promoter_id:
        from app.models.promoter import Promoter
        p_row = await db.execute(select(Promoter).where(Promoter.id == promoter_id))
        promoter = p_row.scalar_one_or_none()
        if promoter and promoter.custom_price:
            # 推广员自定义价格
            amount = promoter.custom_price
            base_price = UNLOCK_PRICE
            markup = amount - base_price
            if markup < 0:
                markup = Decimal("0")

    # 创建订单
    order_no = gen_order_no()
    order = Order(
        order_no=order_no,
        user_id=user_id,
        assessment_id=assessment_id,
        promoter_id=promoter_id,
        amount=amount,
        base_price=base_price,
        markup=markup,
        status="pending",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    logger.info(f"order created: no={order_no} assessment_id={assessment_id} amount={amount}")
    return ok({
        "order_no": order.order_no,
        "amount": float(order.amount),
        "status": order.status,
        "base_price": float(order.base_price),
        "markup": float(order.markup),
    })


@router.post("/mock-pay/{order_no}", summary="模拟支付（点解锁按钮直接调用，2 秒后回调）")
async def mock_pay(
    order_no: str = Path(..., min_length=1),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    模拟支付：用于 UI 联调，不接真实微信支付
    立即返回 pending，前端轮询 /api/order/status/{order_no}，2 秒后状态变 paid
    """
    from datetime import datetime

    order = (await db.execute(select(Order).where(Order.order_no == order_no))).scalar_one_or_none()
    if not order:
        raise NotFoundException(f"订单 {order_no} 不存在")
    if order.status == "paid":
        return ok({"order_no": order_no, "status": "paid", "message": "订单已支付"})
    if order.status == "refunded":
        raise ParamException("订单已退款")

    # 立即更新为 paid（实际生产是异步回调）
    order.status = "paid"
    order.pay_method = "mock"
    order.transaction_id = f"MOCK_{order_no}"
    order.paid_at = datetime.utcnow()

    # 解锁报告
    a = await db.get(Assessment, order.assessment_id)
    if a and not a.is_paid:
        a.is_paid = 1
        a.paid_at = order.paid_at

    await db.commit()
    logger.info(f"order mock-paid: {order_no} amount={order.amount}")

    return ok({
        "order_no": order_no,
        "status": "paid",
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "message": "支付成功，报告已解锁",
    })


@router.get("/status/{order_no}", summary="查询订单状态")
async def get_order_status(
    order_no: str = Path(..., min_length=1),
    db: AsyncSession = Depends(get_db),
) -> dict:
    order = (await db.execute(select(Order).where(Order.order_no == order_no))).scalar_one_or_none()
    if not order:
        raise NotFoundException(f"订单 {order_no} 不存在")
    return ok({
        "order_no": order.order_no,
        "status": order.status,
        "amount": float(order.amount),
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    })
