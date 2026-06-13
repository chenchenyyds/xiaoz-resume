"""用户信息 schema"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserInfo(BaseModel):
    id: int
    phone: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    invite_code: Optional[str] = None
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PointSummary(BaseModel):
    """积分余额汇总(三种类型分别)"""
    trial_balance: int = 0
    subscription_balance: int = 0
    purchase_balance: int = 0
    total_balance: int = 0


class UserMeResp(BaseModel):
    user: UserInfo
    points: PointSummary
