"""
评分卡配置 + 纠错规则 + 分享 + 免费体验
"""
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Enum, Index, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ScorecardRule(Base):
    """评分卡规则项"""

    __tablename__ = "scorecard_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 关联银行（NULL = 通用规则，bank_id 和 product_type_id 同时为 NULL = 所有场景都适用）
    bank_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    # 关联产品类型（NULL = 通用规则，X = 该产品专属规则）
    product_type_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    variable: Mapped[str] = mapped_column(String(64), nullable=False)
    option_label: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(default=0, nullable=False)
    # personal / business / both（基础 type）
    type: Mapped[str] = mapped_column(
        Enum("personal", "business", "both", name="scorecard_type"),
        default="both",
        nullable=False,
    )
    is_veto: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enabled: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_score_product", "product_type_id"),
    )


class ValidationRule(Base):
    """纠错规则（实时校验用）"""

    __tablename__ = "validation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_name: Mapped[str] = mapped_column(String(64), nullable=False)
    condition_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str] = mapped_column(
        Enum("info", "warning", "error", name="validation_level"),
        default="warning",
        nullable=False,
    )
    enabled: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)


class Share(Base):
    """分享记录"""

    __tablename__ = "shares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    share_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    clicks: Mapped[int] = mapped_column(default=0, nullable=False)
    new_users: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class FreeTrial(Base):
    """免费体验记录"""

    __tablename__ = "free_trials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sharer_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    assessment_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("idx_scorecard_user", "user_id"),)
