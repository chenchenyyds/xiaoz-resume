"""操作日志埋点工具

在 admin API 中调用 record_admin_log() 即可记录。
"""

import json
from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.operation_log import OperationLog


def record_admin_log(
    db: Session,
    admin: User,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    before_value: Optional[dict] = None,
    after_value: Optional[dict] = None,
    remark: Optional[str] = None,
    request: Optional[Request] = None,
) -> OperationLog:
    """记录一次管理员操作(必须 commit 后才落库)"""
    log = OperationLog(
        admin_id=admin.id,
        admin_phone=admin.phone,
        action=action,
        target_type=target_type,
        target_id=target_id,
        before_value=before_value,
        after_value=after_value,
        remark=remark,
        ip=_get_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(log)
    db.flush()  # 不 commit,由调用方统一 commit
    return log


def _get_client_ip(request: Request) -> Optional[str]:
    """从 X-Forwarded-For 或 client.host 取 IP"""
    if not request:
        return None
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    return request.client.host if request.client else None
