"""后台 - 数据看板 1 个 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_admin
from app.services import admin_service
from app.schemas.admin import DashboardOverview

router = APIRouter(prefix="/dashboard", tags=["后台-数据看板"])


@router.get("/overview", summary="4 个核心指标", response_model=DashboardOverview)
async def overview(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    data = admin_service.get_dashboard(db)
    return DashboardOverview(**data)
