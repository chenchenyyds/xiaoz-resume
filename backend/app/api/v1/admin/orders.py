"""后台 - 订单 3 个 API"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_admin
from app.core.exceptions import BizException, BizCode
from app.services import admin_service, order_service
from app.schemas.admin import AdminOrderListResp, AdminOrderItem, RefundReq
from app.models.user import User

router = APIRouter(prefix="/orders", tags=["后台-订单"])


@router.get("", summary="订单列表", response_model=AdminOrderListResp)
async def list_orders(
    status: Optional[str] = Query(None),
    product_code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    items, total = admin_service.list_orders(db, status, product_code, page, page_size)
    return AdminOrderListResp(
        items=[
            AdminOrderItem(
                order_no=o.order_no,
                user_id=o.user_id,
                user_phone=(
                    getattr(o, "_user", None).phone
                    if getattr(o, "_user", None)
                    else None
                ),
                product_code=o.product_code,
                amount=o.amount,
                pay_amount=o.pay_amount,
                pay_channel=o.pay_channel,
                status=o.status,
                invite_user_id=o.invite_user_id,
                paid_at=o.paid_at,
                refunded_at=o.refunded_at,
                refund_amount=o.refund_amount,
                created_at=o.created_at,
            )
            for o in items
        ],
        total=total,
    )


@router.get("/{order_no}", summary="订单详情", response_model=AdminOrderItem)
async def order_detail(
    order_no: str,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    items, _ = admin_service.list_orders(db)
    for o in items:
        if o.order_no == order_no:
            return AdminOrderItem(
                order_no=o.order_no,
                user_id=o.user_id,
                user_phone=o.user.phone if o.user else None,
                product_code=o.product_code,
                amount=o.amount,
                pay_amount=o.pay_amount,
                pay_channel=o.pay_channel,
                status=o.status,
                invite_user_id=o.invite_user_id,
                paid_at=o.paid_at,
                refunded_at=o.refunded_at,
                refund_amount=o.refund_amount,
                created_at=o.created_at,
            )
    raise BizException(BizCode.NOT_FOUND, "订单不存在")


@router.post("/{order_no}/refund", summary="退款")
async def refund(
    order_no: str,
    req: RefundReq,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return order_service.refund_order(db, order_no, req.amount, req.reason)
