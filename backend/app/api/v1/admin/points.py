"""积分流水管理 API(后台)"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import get_current_admin
from app.core.exceptions import BizException, BizCode
from app.models.user import User
from app.models.point import PointTransaction

router = APIRouter(prefix="/admin/points", tags=["后台-积分流水"])


@router.get("/transactions", summary="积分流水列表")
async def list_transactions(
    user_id: Optional[int] = Query(None, description="按用户 ID 筛选"),
    phone: Optional[str] = Query(None, description="按手机号筛选"),
    feature: Optional[str] = Query(
        None, description="按功能筛选:partial_rewrite/full_rewrite"
    ),
    source: Optional[str] = Query(
        None, description="按来源:order/rewrite/redeem/trial/invite/adjust/refund"
    ),
    change_type: Optional[str] = Query(None, description="earn/spend(获得/消耗)"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """积分流水列表,支持多维度筛选 + 分页"""
    q = db.query(PointTransaction)

    # 筛选条件
    if user_id:
        q = q.filter(PointTransaction.user_id == user_id)
    elif phone:
        u = db.query(User).filter(User.phone == phone).first()
        if not u:
            raise BizException(BizCode.NOT_FOUND, "用户不存在")
        q = q.filter(PointTransaction.user_id == u.id)

    if feature:
        q = q.filter(PointTransaction.feature == feature)
    if source:
        q = q.filter(PointTransaction.source == source)
    if change_type == "earn":
        q = q.filter(PointTransaction.change > 0)
    elif change_type == "spend":
        q = q.filter(PointTransaction.change < 0)

    if start_date:
        q = q.filter(PointTransaction.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        q = q.filter(
            PointTransaction.created_at
            <= datetime.fromisoformat(end_date) + timedelta(days=1)
        )

    total = q.count()
    items = (
        q.order_by(desc(PointTransaction.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # 关联用户手机号
    user_map = {}
    if items:
        user_ids = list({i.user_id for i in items})
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        user_map = {u.id: u.phone for u in users}

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": t.id,
                    "user_id": t.user_id,
                    "user_phone": user_map.get(t.user_id, "未知"),
                    "point_type": t.point_type,
                    "change": t.change,
                    "balance_before": t.balance_before,
                    "balance_after": t.balance_after,
                    "source": t.source,
                    "feature": t.feature,
                    "related_id": t.related_id,
                    "remark": t.remark,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in items
            ],
        },
    }


@router.get("/stats", summary="积分流水统计")
async def stats(
    days: int = Query(7, ge=1, le=90, description="统计最近 N 天"),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """积分发放/消耗统计,按日聚合"""
    start = datetime.utcnow() - timedelta(days=days)
    transactions = (
        db.query(PointTransaction).filter(PointTransaction.created_at >= start).all()
    )

    # 按日聚合
    daily = {}
    for t in transactions:
        day = t.created_at.strftime("%Y-%m-%d")
        if day not in daily:
            daily[day] = {"earned": 0, "spent": 0, "earn_count": 0, "spend_count": 0}
        if t.change > 0:
            daily[day]["earned"] += t.change
            daily[day]["earn_count"] += 1
        else:
            daily[day]["spent"] += abs(t.change)
            daily[day]["spend_count"] += 1

    # 按来源聚合
    by_source = {}
    for t in transactions:
        src = t.source or "unknown"
        if src not in by_source:
            by_source[src] = {"earned": 0, "spent": 0}
        if t.change > 0:
            by_source[src]["earned"] += t.change
        else:
            by_source[src]["spent"] += abs(t.change)

    # 按类型聚合
    by_point_type = {}
    for t in transactions:
        pt = t.point_type
        if pt not in by_point_type:
            by_point_type[pt] = {"earned": 0, "spent": 0, "balance": 0}
        if t.change > 0:
            by_point_type[pt]["earned"] += t.change
        else:
            by_point_type[pt]["spent"] += abs(t.change)
        by_point_type[pt]["balance"] = t.balance_after or 0

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "days": days,
            "total_earned": sum(t.change for t in transactions if t.change > 0),
            "total_spent": sum(abs(t.change) for t in transactions if t.change < 0),
            "transaction_count": len(transactions),
            "daily": [{"date": k, **v} for k, v in sorted(daily.items())],
            "by_source": by_source,
            "by_point_type": by_point_type,
        },
    }


@router.post("/adjust", summary="调整用户积分(管理员)")
async def adjust_user_points(
    user_id: int,
    delta: int,
    remark: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """管理员手动调整用户积分(补偿、修复等场景)"""
    from app.services.points_service import grant_points, consume_points

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BizException(BizCode.NOT_FOUND, "用户不存在")

    if delta == 0:
        raise BizException(BizCode.BAD_REQUEST, "调整数量不能为 0")

    if delta > 0:
        # 增加积分(标记为 adjust 来源)
        grant_points(
            db,
            user_id=user_id,
            points=delta,
            point_type="purchase",
            source="adjust",
            remark=f"管理员 {admin.phone} 调整:+{delta} {remark}",
        )
    else:
        # 扣减积分(优先消耗即将过期的)
        consume_points(
            db,
            user_id=user_id,
            points=abs(delta),
            feature="adjust",
            remark=f"管理员 {admin.phone} 调整:-{abs(delta)} {remark}",
        )

    return {
        "code": 0,
        "message": "ok",
        "data": {"user_id": user_id, "delta": delta, "remark": remark},
    }
