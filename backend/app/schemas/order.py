"""订单相关 schema"""

from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class CreateOrderReq(BaseModel):
    product_code: str = Field(..., description="single/monthly/points_1000")
    invite_code: Optional[str] = Field(default=None, description="推广码")


class CreateOrderResp(BaseModel):
    order_no: str
    amount: Decimal
    pay_url: str  # 虎皮椒支付链接


class OrderItem(BaseModel):
    order_no: str
    product_code: str
    amount: Decimal
    pay_amount: Optional[Decimal]
    status: str
    created_at: datetime
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderListResp(BaseModel):
    items: list[OrderItem]
    total: int


class HupijiaoNotifyReq(BaseModel):
    """虎皮椒回调字段(实际用 Form)"""

    merchant: str
    order_no: str
    amount: str
    pay_trade_no: str
    status: str  # paid/...
    sign: str
    # 其他字段
