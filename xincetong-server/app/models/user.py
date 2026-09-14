"""
用户表模型
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """普通用户 / 推广员 / 管理员 统一一张表，按 role 区分"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    unionid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        Enum("user", "promoter", "admin", name="user_role"),
        default="user",
        nullable=False,
    )
    inviter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    promoter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[int] = mapped_column(default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_openid", "openid"),
        Index("idx_user_promoter", "promoter_id"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} openid={self.openid} role={self.role}>"
