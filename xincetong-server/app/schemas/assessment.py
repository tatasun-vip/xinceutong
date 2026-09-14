"""
测评相关 Pydantic 模型
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# 通用
# ============================================================================


class ApiResponse(BaseModel):
    """统一 API 响应"""

    code: int = Field(..., description="0=成功")
    message: str = Field(..., description="提示信息")
    data: Any | None = None


# ============================================================================
# 实时纠错
# ============================================================================


class ValidateRequest(BaseModel):
    step: int = Field(..., ge=1, le=5, description="当前步骤 1-5")
    data: dict = Field(..., description="当前步骤填写的数据")
    type: str = Field(default="personal", description="personal/business")
    prev_data: dict | None = Field(default=None, description="之前步骤的数据（用于跨步骤校验）")


class ValidationItem(BaseModel):
    rule_name: str
    level: str  # info/warning/error
    message: str


class ValidateResponse(BaseModel):
    valid: bool = Field(..., description="True=无 error 级问题")
    items: list[ValidationItem] = []
    has_warning: bool = False
    has_error: bool = False


# ============================================================================
# 提交测评
# ============================================================================


class AssessmentSubmitRequest(BaseModel):
    type: str = Field(..., description="personal/business")
    input_data: dict = Field(..., description="用户填写的全部数据")
    share_code: str | None = None
    promoter_code: str | None = None


class AssessmentSubmitResponse(BaseModel):
    assessment_id: int
    report_no: str
    score: int
    level: str
    limit_min: int
    limit_max: int
    rate_min: float
    rate_max: float
    pass_probability: str
    free_summary: str
    is_paid: bool = False
    risk_tags: list[str] = []
    advantages: list[str] = []
    weak_points: list[str] = []
    products_preview: list[dict] = []  # 免费结果只展示 1-2 个产品名
    veto: dict | None = None
    disclaimer: str = "本结果为模拟评分，不查征信、不构成贷款承诺。实际审批以金融机构为准。"


# ============================================================================
# 查结果
# ============================================================================


class FreeResultResponse(BaseModel):
    assessment_id: int
    report_no: str
    score: int
    level: str
    limit_min: int
    limit_max: int
    rate_min: float
    rate_max: float
    pass_probability: str
    free_summary: str
    is_paid: bool
    created_at: datetime
