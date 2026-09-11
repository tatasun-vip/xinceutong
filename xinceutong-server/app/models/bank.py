"""
银行模型（多租户基础）

- Bank: 银行主表（10 家起步：工/建/招/微众/网商/中/农/交/平安/新网）
- BankFormSchema: 每家银行的动态表单 schema（每步 1 条记录）
- BankProduct: 每家银行的推荐产品
"""
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Enum, Index, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Bank(Base):
    """银行主表"""

    __tablename__ = "banks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 银行编码（业务用，全大写英文 + 数字）：ICBC / CCB / CMB / WEBANK / MYBANK / BOC / ABC / BCM / PAB / XCB
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    # 中文名：工商银行
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    # 简称
    short_name: Mapped[str] = mapped_column(String(32), nullable=False)
    # 英文名
    en_name: Mapped[str] = mapped_column(String(64), nullable=True)
    # 类型：state_owned(国有大行) / joint_stock(股份制) / internet(互联网) / policy(政策性)
    type: Mapped[str] = mapped_column(
        Enum("state_owned", "joint_stock", "internet", "policy", "city_commercial", name="bank_type"),
        nullable=False,
    )
    # logo URL
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 简短介绍
    short_desc: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 详细描述（长文）
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 银行特点（标签数组 JSON）
    features: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # 准入标语（slogan）
    slogan: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 主色调（前端展示用 hex）
    brand_color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # 状态
    enabled: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    # 排序
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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
        Index("idx_bank_type", "type"),
        Index("idx_bank_enabled", "enabled"),
    )

    def __repr__(self) -> str:
        return f"<Bank code={self.code} name={self.name}>"


class BankFormSchema(Base):
    """每家银行的动态表单 schema（每步 1 条，fields_json 是字段数组）"""

    __tablename__ = "bank_form_schemas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_id: Mapped[int] = mapped_column(Integer, nullable=False)  # 关联 banks.id
    # 步骤编号：1~5
    step_no: Mapped[int] = mapped_column(Integer, nullable=False)
    # 步骤标题（中文）
    step_title: Mapped[str] = mapped_column(String(64), nullable=False)
    # 步骤副标题
    step_subtitle: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 步骤英文标签
    step_label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # 字段数组 JSON，结构示例：
    # [
    #   {"key": "age", "label": "年龄", "type": "number", "required": true, "min": 18, "max": 65, "unit": "岁"},
    #   {"key": "city_tier", "label": "城市层级", "type": "select", "required": true,
    #    "options": [{"value": "t1", "label": "一线"}, ...]},
    #   {"key": "housing", "label": "住房情况", "type": "radio", "required": true,
    #    "options": [{"value": "owned", "label": "自有"}, {"value": "rent", "label": "租赁"}]},
    #   {"key": "income", "label": "月收入", "type": "slider", "required": true, "min": 0, "max": 100000, "step": 1000, "unit": "元"},
    # ]
    fields_json: Mapped[list] = mapped_column(JSON, nullable=False)
    # 是否启用
    enabled: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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
        Index("idx_schema_bank", "bank_id"),
        Index("idx_schema_step", "bank_id", "step_no"),
    )

    def __repr__(self) -> str:
        return f"<BankFormSchema bank_id={self.bank_id} step={self.step_no}>"


class BankProduct(Base):
    """每家银行的推荐产品"""

    __tablename__ = "bank_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 产品名称
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    # 产品副标题
    subtitle: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 额度下限（万元）
    limit_min: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 额度上限（万元）
    limit_max: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 利率下限（年化 %）
    rate_min: Mapped[float] = mapped_column(default=0.0, nullable=False)
    # 利率上限（年化 %）
    rate_max: Mapped[float] = mapped_column(default=0.0, nullable=False)
    # 通过分数下限（达到此分数才推荐）
    pass_score_min: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 通过分数上限
    pass_score_max: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    # 产品特色标签
    features: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # 申请条件简述
    requirement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 是否推荐（高优展示）
    recommend: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    enabled: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_product_bank", "bank_id"),
    )

    def __repr__(self) -> str:
        return f"<BankProduct bank_id={self.bank_id} name={self.name}>"
