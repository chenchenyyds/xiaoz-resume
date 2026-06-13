"""后台 - 用户 4 个 API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_admin
from app.services import admin_service
from app.schemas.admin import (
    AdminUserListResp, AdminUserItem, AdminUserDetail,
    AdjustPointsReq, DisableUserReq,
)

router = APIRouter(prefix="/users", tags=["后台-用户"])


@router.get("", summary="用户列表", response_model=AdminUserListResp)
async def list_users(
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    items, total = admin_service.list_users(db, keyword, status, page, page_size)
    return AdminUserListResp(items=[AdminUserItem(**u) for u in items], total=total)


@router.get("/{user_id}", summary="用户详情", response_model=AdminUserDetail)
async def user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    data = admin_service.get_user_detail(db, user_id)
    return AdminUserDetail(**data)


@router.post("/{user_id}/disable", summary="禁用用户")
async def disable(
    user_id: int,
    req: DisableUserReq = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return admin_service.disable_user(db, user_id, req.reason if req else None)


@router.post("/{user_id}/enable", summary="启用用户")
async def enable(
    user_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return admin_service.enable_user(db, user_id)


@router.post("/{user_id}/adjust-points", summary="调整积分")
async def adjust_points(
    user_id: int,
    req: AdjustPointsReq,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return admin_service.adjust_user_points(db, user_id, req.change, req.point_type, req.reason)
