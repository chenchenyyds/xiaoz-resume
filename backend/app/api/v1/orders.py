"""订单 API - 用户端 2 个(创建订单 + 支付链接) + 1 个回调"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import order_service
from app.schemas.order import CreateOrderReq, CreateOrderResp

router = APIRouter(prefix="/orders", tags=["订单"])


@router.post("", summary="创建订单", response_model=CreateOrderResp)
async def create(
    req: CreateOrderReq,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = order_service.create_order(db, user.id, req.product_code, req.invite_code)
    return CreateOrderResp(
        order_no=result["order_no"],
        amount=result["amount"],
        pay_url=result["pay_url"],
    )


@router.get("/{order_no}/pay-url", summary="获取订单支付链接")
async def get_pay_url(
    order_no: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.order import Order

    order = (
        db.query(Order)
        .filter(Order.order_no == order_no, Order.user_id == user.id)
        .first()
    )
    if not order:
        from app.core.exceptions import BizException, BizCode

        raise BizException(BizCode.NOT_FOUND, "订单不存在")
    if order.status != "pending":
        from app.core.exceptions import BizException, BizCode

        raise BizException(BizCode.CONFLICT, f"订单状态 {order.status} 不可支付")
    # 重新创建支付链接
    from app.services import order_service

    cfg = order_service.PRODUCTS.get(order.product_code)
    pay_data = __import__("app.core.payment", fromlist=["create_order"]).create_order(
        order_no=order.order_no,
        product_name=cfg["name"],
        amount=float(order.amount),
    )
    return {"pay_url": pay_data.get("pay_url", "")}


# ---------- 虎皮椒回调(无需鉴权) ----------
@router.post(
    "/hupijiao/notify", summary="虎皮椒支付回调", response_class=PlainTextResponse
)
async def hupijiao_notify(request: Request, db: Session = Depends(get_db)):
    """虎皮椒回调,以 Form 表单提交"""
    form = await request.form()
    params = dict(form)
    logger_msg = f"虎皮椒回调: {params}"
    from loguru import logger

    logger.info(logger_msg)
    result = order_service.handle_hupijiao_notify(db, params)
    return PlainTextResponse(content=result)
