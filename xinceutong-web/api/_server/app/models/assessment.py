"""
测评记录模型
"""
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Enum, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Assessment(Base):
    """单次测评（个人贷 / 企业贷）"""

    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # 关联银行（NULL = 通用测评；保留字段用于方法论/推广素材）
    bank_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    bank_code: Mapped[str | None] = mapped_column(String(16), nullable=True)  # 冗余便于查询
    type: Mapped[str] = mapped_column(
        Enum("personal", "business", name="assessment_type"),
        nullable=False,
    )

    # 用户填写数据（加密 JSON）
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    # ============ 综合分（6 套独立模型加权得出）============
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level: Mapped[str | None] = mapped_column(String(4), nullable=True)
    limit_min: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 单位：元
    limit_max: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 单位：元
    rate_min: Mapped[float | None] = mapped_column(nullable=True)
    rate_max: Mapped[float | None] = mapped_column(nullable=True)
    pass_probability: Mapped[str | None] = mapped_column(String(8), nullable=True)
    risk_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    advantages: Mapped[list | None] = mapped_column(JSON, nullable=True)
    weak_points: Mapped[list | None] = mapped_column(JSON, nullable=True)
    suggestions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # v3.2 核心问题（按严重度排序，最多 3 个，含 5 维度展开）
    top_issues: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # v3.2 改善后推演（按建议执行 90 天后的预测评分/额度/通过率）
    improvement_projection: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # v5 P0 4 维度分（business 专用；personal 存 null）
    # 结构：{
    #   "legal_person": { "raw": 14, "max": 18, "ratio": 77.8, "weight": "30%" },
    #   "enterprise":   { "raw": 48, "max": 60, "ratio": 80.0, "weight": "40%" },
    #   "compliance":   { "raw": 20, "max": 20, "ratio": 100.0, "weight": "20%" },
    #   "industry":     { "raw": 8,  "max": 10, "ratio": 80.0, "weight": "10%" },
    #   "total":        84.0
    # }
    # 注意：依赖生产 DB 跑过 0002_business_dimensions.sql（PostgreSQL 优先）加 dimensions 列
    dimensions: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # ============ 6 大产品独立测算结果（v3 新增）============
    # 结构：[
    #   {
    #     "product_code": "quality_unit",
    #     "product_name": "优质单位贷",
    #     "score": 82,
    #     "level": "A",
    #     "limit_min": 150000,
    #     "limit_max": 200000,
    #     "rate_min": 4.2,
    #     "rate_max": 5.5,
    #     "pass_probability": "高",
    #     "formula_used": "quality_unit_income",
    #     "key_points": [...],
    #     "matched_items": [...],
    #     "risk_tags": [...]
    #   },
    #   ...
    # ]
    product_results: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # 兼容字段：原 products 字段保留（按等级推荐的产品列表，报告页"老版本"展示）
    products: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # ============ 付费状态 ============
    is_paid: Mapped[int] = mapped_column(default=0, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 完整报告 Markdown（付费后生成，缓存用）
    full_report: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_assessment_user", "user_id"),
        Index("idx_report_no", "report_no"),
    )

    def __repr__(self) -> str:
        return f"<Assessment id={self.id} no={self.report_no} type={self.type}>"
