"""
分佣记录模型
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Enum, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Commission(Base):
    """分佣流水（每笔订单一条）"""

    __tablename__ = "commissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    promoter_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    base_commission: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    markup_commission: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    total_commission: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    platform_income: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)

    status: Mapped[str] = mapped_column(
        Enum("pending", "settled", "frozen", name="commission_status"),
        default="pending",
        nullable=False,
    )
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
