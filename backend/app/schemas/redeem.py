"""兑换码相关 schema"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RedeemReq(BaseModel):
    code: str = Field(..., min_length=8, max_length=32)


class RedeemResp(BaseModel):
    type: str
    points: int
    valid_days: int
    points_balance: int


class GenerateCodeReq(BaseModel):
    type: str = Field(..., description="single/monthly/points_1000")
    count: int = Field(..., ge=1, le=1000)
    batch_id: Optional[str] = None
    valid_days: int = Field(default=365, ge=1, le=730)


class GenerateCodeResp(BaseModel):
    batch_id: str
    count: int
    codes: List[str]  # 明文,只这次返回


class CodeListItem(BaseModel):
    id: int
    code_mask: str
    type: str
    points: int
    status: str
    batch_id: Optional[str]
    user_id: Optional[int]
    used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class CodeListResp(BaseModel):
    items: list[CodeListItem]
    total: int
