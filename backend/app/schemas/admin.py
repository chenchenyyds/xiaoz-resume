"""后台管理 schema"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ---------- 数据看板 ----------
class DashboardOverview(BaseModel):
    today_dau: int
    today_orders: int
    today_revenue: Decimal
    today_llm_cost: Decimal
    total_users: int
    total_orders: int
    total_revenue: Decimal


# ---------- 订单 ----------
class AdminOrderItem(BaseModel):
    order_no: str
    user_id: Optional[int]
    user_phone: Optional[str] = None
    product_code: str
    amount: Decimal
    pay_amount: Optional[Decimal]
    pay_channel: Optional[str]
    status: str
    invite_user_id: Optional[int]
    paid_at: Optional[datetime]
    refunded_at: Optional[datetime]
    refund_amount: Optional[Decimal]
    created_at: datetime


class AdminOrderListResp(BaseModel):
    items: List[AdminOrderItem]
    total: int


class RefundReq(BaseModel):
    amount: Optional[Decimal] = None  # None=全额
    reason: str


# ---------- 用户 ----------
class AdminUserItem(BaseModel):
    id: int
    phone: str
    nickname: Optional[str]
    status: str
    is_admin: bool
    invite_user_id: Optional[int]
    invite_code: Optional[str]
    total_points_earned: int
    total_points_used: int
    total_orders: int
    total_spent: Decimal
    created_at: datetime
    last_active_at: Optional[datetime]


class AdminUserListResp(BaseModel):
    items: List[AdminUserItem]
    total: int


class AdminUserDetail(AdminUserItem):
    point_transactions: List[dict]
    recent_orders: List[AdminOrderItem]


class AdjustPointsReq(BaseModel):
    change: int  # 正=加分,负=减分
    point_type: str = "purchase"  # 调整到哪类账户
    reason: str


# ---------- 兑换码 ----------
class AdminCodeListResp(BaseModel):
    items: List[dict]
    total: int


# ---------- 通用 ----------
class DisableUserReq(BaseModel):
    reason: Optional[str] = None
