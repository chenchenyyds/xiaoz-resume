"""后台管理服务：看板、订单、用户、兑换码查询"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from app.models.user import User
from app.models.order import Order
from app.models.redeem import RedeemCode
from app.models.point import PointAccount, PointTransaction
from app.models.rewrite import RewriteRecord
from app.core.exceptions import BizException, BizCode


# ============================================
# 数据看板
# ============================================
def get_dashboard(db: Session) -> dict:
    """4 个核心指标 + 累计"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 今日订单
    today_orders = (
        db.query(Order)
        .filter(
            Order.created_at >= today_start,
            Order.status == "paid",
        )
        .all()
    )
    today_revenue = sum((o.pay_amount or o.amount) for o in today_orders)
    today_count = len(today_orders)

    # 今日活跃用户(last_active_at 在 today 之后)
    today_dau = db.query(User).filter(User.last_active_at >= today_start).count()

    # 今日 LLM 成本(简化估算:输入+输出 token,按 2 元/百万 token)
    today_records = (
        db.query(RewriteRecord).filter(RewriteRecord.created_at >= today_start).all()
    )
    total_tokens = sum(
        (r.input_tokens or 0) + (r.output_tokens or 0) for r in today_records
    )
    today_llm_cost = Decimal(str(round(total_tokens / 1000000 * 2, 4)))

    # 累计
    total_users = db.query(User).count()
    total_orders = db.query(Order).filter(Order.status == "paid").count()
    total_revenue = db.query(func.coalesce(func.sum(Order.pay_amount), 0)).filter(
        Order.status == "paid"
    ).scalar() or Decimal("0")

    return {
        "today_dau": today_dau,
        "today_orders": today_count,
        "today_revenue": today_revenue,
        "today_llm_cost": today_llm_cost,
        "total_users": total_users,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
    }


# ============================================
# 订单管理
# ============================================
def list_orders(
    db: Session,
    status: Optional[str] = None,
    product_code: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list, int]:
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if product_code:
        q = q.filter(Order.product_code == product_code)
    total = q.count()
    items = (
        q.order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # 关联用户手机号
    user_ids = list({o.user_id for o in items if o.user_id})
    users = (
        {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()}
        if user_ids
        else {}
    )
    for o in items:
        o._user = users.get(o.user_id) if o.user_id else None
    return items, total


# ============================================
# 用户管理
# ============================================
def list_users(
    db: Session,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list, int]:
    q = db.query(User)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter((User.phone.like(like)) | (User.nickname.like(like)))
    if status:
        q = q.filter(User.status == status)
    total = q.count()
    users = (
        q.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # 聚合每个用户的积分和订单数据
    user_ids = [u.id for u in users]
    point_stats = {}
    if user_ids:
        rows = (
            db.query(
                PointAccount.user_id,
                func.coalesce(func.sum(PointAccount.total_earned), 0).label("earned"),
                func.coalesce(func.sum(PointAccount.total_used), 0).label("used"),
            )
            .filter(PointAccount.user_id.in_(user_ids))
            .group_by(PointAccount.user_id)
            .all()
        )
        point_stats = {r.user_id: (r.earned, r.used) for r in rows}

    order_stats = {}
    if user_ids:
        rows = (
            db.query(
                Order.user_id,
                func.count(Order.id).label("cnt"),
                func.coalesce(func.sum(Order.pay_amount), 0).label("total"),
            )
            .filter(Order.user_id.in_(user_ids), Order.status == "paid")
            .group_by(Order.user_id)
            .all()
        )
        order_stats = {r.user_id: (r.cnt, r.total) for r in rows}

    result = []
    for u in users:
        earned, used = point_stats.get(u.id, (0, 0))
        cnt, total = order_stats.get(u.id, (0, 0))
        result.append(
            {
                "id": u.id,
                "phone": u.phone,
                "nickname": u.nickname,
                "status": u.status,
                "is_admin": u.is_admin,
                "invite_user_id": u.invite_user_id,
                "invite_code": u.invite_code,
                "total_points_earned": int(earned),
                "total_points_used": int(used),
                "total_orders": cnt,
                "total_spent": total or Decimal("0"),
                "created_at": u.created_at,
                "last_active_at": u.last_active_at,
            }
        )
    return result, total


def get_user_detail(db: Session, user_id: int) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BizException(BizCode.NOT_FOUND, "用户不存在")

    # 积分流水(最近 20 条)
    txns = (
        db.query(PointTransaction)
        .filter(PointTransaction.user_id == user_id)
        .order_by(PointTransaction.created_at.desc())
        .limit(20)
        .all()
    )

    # 最近订单
    orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    # 聚合
    point_stats = (
        db.query(
            func.coalesce(func.sum(PointAccount.total_earned), 0),
            func.coalesce(func.sum(PointAccount.total_used), 0),
        )
        .filter(PointAccount.user_id == user_id)
        .first()
    )
    earned, used = point_stats or (0, 0)
    order_stats = (
        db.query(
            func.count(Order.id),
            func.coalesce(func.sum(Order.pay_amount), 0),
        )
        .filter(Order.user_id == user_id, Order.status == "paid")
        .first()
    )
    cnt, total = order_stats or (0, 0)

    return {
        "id": user.id,
        "phone": user.phone,
        "nickname": user.nickname,
        "status": user.status,
        "is_admin": user.is_admin,
        "invite_user_id": user.invite_user_id,
        "invite_code": user.invite_code,
        "total_points_earned": int(earned),
        "total_points_used": int(used),
        "total_orders": cnt,
        "total_spent": total or Decimal("0"),
        "created_at": user.created_at,
        "last_active_at": user.last_active_at,
        "point_transactions": [
            {
                "id": t.id,
                "point_type": t.point_type,
                "change": t.change,
                "balance_after": t.balance_after,
                "source": t.source,
                "feature": t.feature,
                "remark": t.remark,
                "created_at": t.created_at,
            }
            for t in txns
        ],
        "recent_orders": [
            {
                "order_no": o.order_no,
                "user_id": o.user_id,
                "user_phone": user.phone,
                "product_code": o.product_code,
                "amount": o.amount,
                "pay_amount": o.pay_amount,
                "pay_channel": o.pay_channel,
                "status": o.status,
                "invite_user_id": o.invite_user_id,
                "paid_at": o.paid_at,
                "refunded_at": o.refunded_at,
                "refund_amount": o.refund_amount,
                "created_at": o.created_at,
            }
            for o in orders
        ],
    }


def disable_user(db: Session, user_id: int, reason: Optional[str] = None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BizException(BizCode.NOT_FOUND, "用户不存在")
    user.status = "disabled"
    db.commit()
    return {"id": user_id, "status": "disabled", "reason": reason}


def enable_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BizException(BizCode.NOT_FOUND, "用户不存在")
    user.status = "active"
    db.commit()
    return {"id": user_id, "status": "active"}


def adjust_user_points(
    db: Session,
    user_id: int,
    change: int,
    point_type: str = "purchase",
    reason: str = "",
):
    """调整用户积分(后台)"""
    from app.services import points_service

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BizException(BizCode.NOT_FOUND, "用户不存在")

    if change > 0:
        points_service.grant_points(
            db,
            user_id=user_id,
            point_type=point_type,
            amount=change,
            source="admin_adjust",
            feature="admin",
            remark=f"管理员调整: {reason}",
        )
    elif change < 0:
        # 负向调整:直接扣
        from app.models.point import PointAccount

        acc = (
            db.query(PointAccount)
            .filter(
                PointAccount.user_id == user_id,
                PointAccount.point_type == point_type,
                PointAccount.balance > 0,
            )
            .order_by(PointAccount.created_at.asc())
            .first()
        )
        if not acc:
            raise BizException(
                BizCode.INSUFFICIENT_POINTS, f"用户没有 {point_type} 积分可扣"
            )
        if acc.balance < abs(change):
            raise BizException(
                BizCode.INSUFFICIENT_POINTS,
                f"积分不足,当前 {acc.balance},要扣 {abs(change)}",
            )
        acc.balance += change  # change 是负的
        acc.total_used += abs(change)
        from app.models.point import PointTransaction

        db.add(
            PointTransaction(
                user_id=user_id,
                point_type=point_type,
                change=change,
                balance_before=acc.balance - change,
                balance_after=acc.balance,
                source="admin_adjust",
                feature="admin",
                remark=f"管理员调整: {reason}",
            )
        )
    db.commit()
    return {"user_id": user_id, "change": change, "point_type": point_type}


# ============================================
# 兑换码管理
# ============================================
def list_codes(
    db: Session,
    batch_id: Optional[str] = None,
    status: Optional[str] = None,
    type_: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list, int]:
    q = db.query(RedeemCode)
    if batch_id:
        q = q.filter(RedeemCode.batch_id == batch_id)
    if status:
        q = q.filter(RedeemCode.status == status)
    if type_:
        q = q.filter(RedeemCode.type == type_)
    total = q.count()
    items = (
        q.order_by(RedeemCode.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total
