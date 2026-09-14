"""
订单模型
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Enum, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Order(Base):
    """支付订单"""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    assessment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    promoter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # 金额相关一律 Decimal（元）
    amount: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    base_price: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("9.99"), nullable=False
    )
    markup: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0"), nullable=False
    )

    status: Mapped[str] = mapped_column(
        Enum("pending", "paid", "refunded", "failed", name="order_status"),
        default="pending",
        nullable=False,
    )
    pay_method: Mapped[str | None] = mapped_column(String(16), nullable=True)
    transaction_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_order_user", "user_id"),
        Index("idx_promoter", "promoter_id"),
        Index("idx_status", "status"),
    )
