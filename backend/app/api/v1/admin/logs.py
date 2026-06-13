"""操作日志 API(后台)

记录管理员的所有敏感操作,便于审计。
- 退款 / 禁用用户 / 调整积分 / 生成兑换码 / 作废兑换码
"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import get_current_admin
from app.core.exceptions import BizException, BizCode
from app.models.user import User
from app.models.operation_log import OperationLog

router = APIRouter(prefix="/admin/logs", tags=["后台-操作日志"])


@router.get("", summary="操作日志列表")
async def list_logs(
    admin_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None, description="操作类型:refund/disable_user/adjust_points/generate_codes/revoke_code"),
    target_type: Optional[str] = Query(None, description="目标类型:order/user/code"),
    target_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    q = db.query(OperationLog)

    if admin_id:
        q = q.filter(OperationLog.admin_id == admin_id)
    if action:
        q = q.filter(OperationLog.action == action)
    if target_type:
        q = q.filter(OperationLog.target_type == target_type)
    if target_id:
        q = q.filter(OperationLog.target_id == target_id)
    if start_date:
        q = q.filter(OperationLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        q = q.filter(OperationLog.created_at <= datetime.fromisoformat(end_date) + timedelta(days=1))

    total = q.count()
    items = q.order_by(desc(OperationLog.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    # 关联管理员手机号
    admin_map = {}
    if items:
        admin_ids = list({i.admin_id for i in items})
        admins = db.query(User).filter(User.id.in_(admin_ids)).all()
        admin_map = {a.id: a.phone for a in admins}

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": i.id,
                    "admin_id": i.admin_id,
                    "admin_phone": admin_map.get(i.admin_id, "未知"),
                    "action": i.action,
                    "target_type": i.target_type,
                    "target_id": i.target_id,
                    "before_value": i.before_value,
                    "after_value": i.after_value,
                    "remark": i.remark,
                    "ip": i.ip,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                }
                for i in items
            ],
        },
    }


@router.get("/stats", summary="操作日志统计")
async def stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """管理员操作频率统计"""
    start = datetime.utcnow() - timedelta(days=days)
    logs = db.query(OperationLog).filter(OperationLog.created_at >= start).all()

    # 按管理员聚合
    by_admin = {}
    for log in logs:
        a = log.admin_id
        by_admin.setdefault(a, {"count": 0, "actions": {}})
        by_admin[a]["count"] += 1
        by_admin[a]["actions"][log.action] = by_admin[a]["actions"].get(log.action, 0) + 1

    # 按 action 聚合
    by_action = {}
    for log in logs:
        by_action[log.action] = by_action.get(log.action, 0) + 1

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "days": days,
            "total_actions": len(logs),
            "by_action": by_action,
            "by_admin": by_admin,
        },
    }
