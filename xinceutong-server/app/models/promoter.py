"""
推广员 & 推广链接 模型
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Enum, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Promoter(Base):
    """推广员资料"""

    __tablename__ = "promoters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    real_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 身份证号加密存储
    id_card_encrypted: Mapped[str | None] = mapped_column(String(255), nullable=True)
    org_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    years: Mapped[int] = mapped_column(default=0, nullable=False)

    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected", "banned", name="promoter_status"),
        default="pending",
        nullable=False,
    )

    commission_rate: Mapped[Decimal] = mapped_column(
        default=Decimal("0.30"), nullable=False
    )
    custom_price: Mapped[Decimal] = mapped_column(
        default=Decimal("9.99"), nullable=False
    )
    total_earnings: Mapped[Decimal] = mapped_column(
        default=Decimal("0"), nullable=False
    )
    balance: Mapped[Decimal] = mapped_column(default=Decimal("0"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PromoterLink(Base):
    """推广链接（一个推广员可建多个渠道）"""

    __tablename__ = "promoter_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    promoter_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    clicks: Mapped[int] = mapped_column(default=0, nullable=False)
    assessments: Mapped[int] = mapped_column(default=0, nullable=False)
    payments: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("idx_code", "code"),)
