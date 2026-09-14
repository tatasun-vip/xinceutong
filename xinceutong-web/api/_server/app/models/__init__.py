"""
ORM 模型集中注册（让 Base.metadata.create_all 全部识别）
"""
# 顺序：被外键引用的先 import
from app.models.bank import Bank, BankFormSchema, BankProduct  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.assessment import Assessment  # noqa: F401
from app.models.product_type import ProductType  # noqa: F401
from app.models.scorecard import ScorecardRule, ValidationRule, Share, FreeTrial  # noqa: F401
from app.models.site_config import SiteConfig  # noqa: F401
from app.models.promoter import Promoter, PromoterLink  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.commission import Commission  # noqa: F401
