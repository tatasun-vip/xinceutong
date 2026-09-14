"""
站点配置表（数字变量化 + 文案变量化）

所有页面/组件中需要运营调整的数字和文案（如 128,000+、50+、9.99）
都从这里读，运营改 DB 即可全站生效。

按 group_name 分类：
  - number: 数字（如 site.user_count）
  - text: 文案（如 site.brand_slogan）
  - compliance: 合规（如 site.disclaimer_short）
"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SiteConfig(Base):
    """站点配置项（key-value）"""

    __tablename__ = "site_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 配置 key（前端用这个查）
    config_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    # 配置 value
    config_value: Mapped[str] = mapped_column(Text, nullable=False)
    # 中文标签（后台管理用）
    config_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 分组：number / text / compliance
    group_name: Mapped[str] = mapped_column(String(32), default="text", nullable=False)
    # 备注
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SiteConfig {self.config_key}={self.config_value}>"
