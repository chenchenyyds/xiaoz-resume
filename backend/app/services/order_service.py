"""订单服务：创建订单、支付回调处理"""
import shortuuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.core.exceptions import BizException, BizCode
from app.core.payment import create_order as hupijiao_create, verify_notify
from app.models.order import Order
from app.models.user import User
from app.services import points_service
from app.services import user_service
from app.services.config_service import get_config_int, get_config_float, get_config
from app.core.config import settings


PRODUCTS = {
    "single": {
        "name": "次卡 500 积分",
        "price_key": "product.single.price",
        "points_key": "product.single.points",
        "valid_days_key": "product.single.valid_days",
        "point_type": "subscription",
    },
    "monthly": {
        "name": "月卡 3000 积分",
        "price_key": "product.monthly.price",
        "points_key": "product.monthly.points",
        "valid_days_key": "product.monthly.valid_days",
        "point_type": "subscription",
    },
    "points_1000": {
        "name": "增购 1000 积分",
        "price_key": "product.points_1000.price",
        "points_key": "product.points_1000.points",
        "valid_days_key": None,  # 永久
        "point_type": "purchase",
    },
}


def get_product_list(db: Session) -> list:
    """给前端展示的商品列表"""
    result = []
    for code, cfg in PRODUCTS.items():
        price = Decimal(get_config(db, cfg["price_key"], "0"))
        points = get_config_int(db, cfg["points_key"], 0)
        valid_days = get_config_int(db, cfg["valid_days_key"], 0) if cfg["valid_days_key"] else 0
        result.append({
            "code": code,
            "name": cfg["name"],
            "price": price,
            "points": points,
            "valid_days": valid_days,
            "description": _product_desc(code, points, valid_days),
        })
    return result


def _product_desc(code: str, points: int, valid_days: int) -> str:
    if code == "single":
        return f"{points} 积分,{valid_days} 天有效,适合试水"
    if code == "monthly":
        return f"{points} 积分,{valid_days} 天有效,约 10 次/天改写,主推"
    if code == "points_1000":
        return f"{points} 积分,永久有效,适合续费过渡"
    return ""


def create_order(
    db: Session,
    user_id: int,
    product_code: str,
    invite_code: Optional[str] = None,
) -> dict:
    """创建订单(返回 order_no + 虎皮椒支付链接)"""
    if product_code not in PRODUCTS:
        raise BizException(BizCode.PARAM_ERROR, "商品不存在")

    cfg = PRODUCTS[product_code]
    price = Decimal(get_config(db, cfg["price_key"], "0"))
    points = get_config_int(db, cfg["points_key"], 0)

    if price <= 0 or points <= 0:
        raise BizException(BizCode.PAY_ERROR, "商品未配置")

    # 推广人
    invite_user_id = None
    if invite_code:
        inviter = user_service.get_by_invite_code(db, invite_code)
        if inviter and inviter.id != user_id:
            invite_user_id = inviter.id

    order_no = f"XZ{datetime.now().strftime('%Y%m%d')}{shortuuid.uuid()[:10].upper()}"
    order = Order(
        order_no=order_no,
        user_id=user_id,
        product_code=product_code,
        amount=price,
        status="pending",
        invite_user_id=invite_user_id,
    )
    db.add(order)
    db.commit()

    # 调虎皮椒下单
    pay_data = hupijiao_create(
        order_no=order_no,
        product_name=cfg["name"],
        amount=float(price),
    )
    pay_url = pay_data.get("pay_url", "")

    return {
        "order_no": order_no,
        "amount": price,
        "pay_url": pay_url,
    }


def handle_hupijiao_notify(db: Session, params: dict) -> str:
    """处理虎皮椒支付回调

    返回 "success" 表示处理成功,虎皮椒会用这个判断是否停止回调
    """
    if not verify_notify(params.copy()):
        logger.warning(f"虎皮椒回调签名校验失败: {params}")
        return "fail"

    order_no = params.get("order_no", "")
    status = params.get("status", "")
    pay_trade_no = params.get("pay_trade_no", "")

    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        logger.warning(f"虎皮椒回调:订单不存在 {order_no}")
        return "fail"

    # 幂等:已支付就忽略
    if order.status == "paid":
        logger.info(f"订单 {order_no} 已支付,忽略重复回调")
        return "success"

    if status != "paid":
        order.status = "closed"
        db.commit()
        return "success"

    # 标记订单为已支付
    order.status = "paid"
    order.pay_amount = order.amount
    order.pay_channel = "hupijiao"
    order.pay_trade_no = pay_trade_no
    order.paid_at = datetime.now(timezone.utc)

    # 加积分
    cfg = PRODUCTS.get(order.product_code)
    if not cfg:
        logger.error(f"订单 {order_no} 商品 {order.product_code} 不在配置中")
        db.commit()
        return "success"

    points = get_config_int(db, cfg["points_key"], 0)
    valid_days = get_config_int(db, cfg["valid_days_key"], 30) if cfg["valid_days_key"] else 0
    expire_at = datetime.now(timezone.utc) + timedelta(days=valid_days) if valid_days > 0 else None

    points_service.grant_points(
        db,
        user_id=order.user_id,
        point_type=cfg["point_type"],
        amount=points,
        source="order",
        feature=order.product_code,
        related_id=order.id,
        remark=f"订单 {order_no} 支付成功",
        expire_at=expire_at,
    )

    # 给推广人发返佣
    if order.invite_user_id and order.invite_user_id != order.user_id:
        _grant_commission(db, order)

    db.commit()
    logger.info(f"订单 {order_no} 支付成功,用户 {order.user_id} 获得 {points} 积分")
    return "success"


def _grant_commission(db: Session, order: Order):
    """给推广人发返佣(V1 只发积分,不打款)"""
    rate_map = {
        "single": "commission.single",
        "monthly": "commission.monthly",
        "points_1000": "commission.purchase",
    }
    rate_key = rate_map.get(order.product_code)
    if not rate_key:
        return
    rate = get_config_float(db, rate_key, 0)
    if rate <= 0:
        return

    # V1 简化:返佣直接以积分形式发放,不打款
    # 积分 = floor(订单金额 * 返佣比例 * 100) 即 1元 = 100 积分
    commission_points = int(float(order.amount) * rate * 100)
    if commission_points <= 0:
        return

    points_service.grant_points(
        db,
        user_id=order.invite_user_id,
        point_type="purchase",  # 增购类型,永久有效
        amount=commission_points,
        source="commission",
        feature="invite_commission",
        related_id=order.id,
        remark=f"订单 {order.order_no} 返佣 {commission_points} 积分",
    )
    logger.info(f"推广人 {order.invite_user_id} 获得返佣 {commission_points} 积分")


def refund_order(db: Session, order_no: str, amount: Optional[Decimal] = None, reason: str = "") -> dict:
    """后台管理员退款"""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise BizException(BizCode.NOT_FOUND, "订单不存在")
    if order.status != "paid":
        raise BizException(BizCode.CONFLICT, f"订单状态 {order.status} 不可退款")

    if amount is None:
        amount = order.pay_amount or order.amount

    order.status = "refunded"
    order.refunded_at = datetime.now(timezone.utc)
    order.refund_amount = amount

    # 退积分:按当时发放的点数比例退
    cfg = PRODUCTS.get(order.product_code)
    if cfg:
        points = get_config_int(db, cfg["points_key"], 0)
        if order.amount and order.amount > 0:
            refund_points_count = int(points * (float(amount) / float(order.amount)))
            if refund_points_count > 0:
                points_service.refund_points(
                    db,
                    user_id=order.user_id,
                    point_type=cfg["point_type"],
                    amount=refund_points_count,
                    source="refund",
                    feature="order_refund",
                    related_id=order.id,
                    remark=f"订单 {order_no} 退款:{reason}",
                )

    db.commit()
    return {"order_no": order_no, "refund_amount": amount}
