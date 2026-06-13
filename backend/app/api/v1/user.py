"""用户 API - 1 个"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import points_service
from app.schemas.user import UserInfo, UserMeResp

router = APIRouter(prefix="/user", tags=["用户"])


@router.get("/me", summary="我的信息", response_model=UserMeResp)
async def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    balance = points_service.get_balance(db, user.id)
    return UserMeResp(
        user=UserInfo(
            id=user.id,
            phone=user.phone,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            invite_code=user.invite_code,
            is_admin=user.is_admin,
            created_at=user.created_at,
        ),
        points=balance,
    )
