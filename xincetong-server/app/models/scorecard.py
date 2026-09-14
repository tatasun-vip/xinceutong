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
    # v17 新增：3 段式评分（加分 / 扣分 / 一票否决）+ 5 维度权重 + 政策性上限
    # is_deduction: 0=加分（命中即加 score）1=扣分（命中即减 score，等同在归一化里 -score）
    is_deduction: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    # dimension: 5 维度之一 credit/debt/asset/personal/public/misc
    #   5 维度满分：信用历史 30 + 偿债能力 30 + 资产负债 20 + 个人特征 15 + 公共信息 5 = 100
    dimension: Mapped[str] = mapped_column(String(16), default="misc", nullable=False)
    # policy_cap: 命中此规则后 final_score 不能超过此等级上界
    #   例：白户 C(54) / 无公积金 B(69) / 关键保障全缺 C(54) / 0 命中 D(39)
    policy_cap: Mapped[str | None] = mapped_column(String(8), nullable=True)
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
        Index("idx_score_dimension", "dimension"),
        Index("idx_score_type", "type"),
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
    # v17 新增：纠错规则也分加扣分（0=提醒 1=扣分提醒）
    is_deduction: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
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
