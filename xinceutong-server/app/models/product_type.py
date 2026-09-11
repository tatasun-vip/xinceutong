"""
6 大产品类型配置

每种产品类型（优质单位贷 / 公积金贷 / 工薪贷 / 有房客户贷 / 纳税贷 / 开票贷）
都有一套独立的模拟审批逻辑：

  - 额度公式（formula）
  - 利率区间（rate_min, rate_max）
  - 重点考察变量（focus_vars）
  - 适用用户类型（user_type: personal / business）
  - 详细说明（description / key_points）
"""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProductType(Base):
    """6 大产品类型配置"""

    __tablename__ = "product_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 业务编码（小写英文+下划线）
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    # 中文名（产品页/报告页展示）
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    # 副标题（卡片小字）
    subtitle: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 适用用户类型：personal / business
    user_type: Mapped[str] = mapped_column(
        Enum("personal", "business", name="product_user_type"),
        nullable=False,
    )
    # 额度公式 key（在 scorecard_engine 中按 key 匹配具体函数）
    # quality_unit_income / housing_fund_mult / salary_income / house_asset / tax_mult / invoice_pct
    limit_formula: Mapped[str] = mapped_column(String(64), nullable=False)
    # 利率下限（年化 %）
    rate_min: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    # 利率上限（年化 %）
    rate_max: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    # 通过概率默认等级（不同时计算时）
    default_pass: Mapped[str] = mapped_column(String(8), default="中", nullable=False)
    # 重点考察变量数组（如 ["company_type", "work_years", "monthly_income"]）
    focus_vars: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # 关键考察点（key_points，文案数组，报告详情页用）
    key_points: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # 适合谁/审批偏好/考察重点（产品页用，Markdown/HTML 都行）
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 排序
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 是否启用
    enabled: Mapped[int] = mapped_column(Boolean, default=True, nullable=False)
    # 是否推荐展示（报告页高亮 ⭐）
    recommend: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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
        Index("idx_pt_user_type", "user_type"),
        Index("idx_pt_enabled", "enabled"),
    )

    def __repr__(self) -> str:
        return f"<ProductType code={self.code} name={self.name}>"
