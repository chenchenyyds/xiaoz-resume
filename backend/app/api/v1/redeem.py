"""兑换码 API - 用户端 1 个"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import redeem_service
from app.schemas.redeem import RedeemReq, RedeemResp

router = APIRouter(prefix="/redeem", tags=["兑换码"])


@router.post("", summary="激活兑换码", response_model=RedeemResp)
async def activate(
    req: RedeemReq,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = redeem_service.activate_code(db, user.id, req.code)
    return RedeemResp(**result)
