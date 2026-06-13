"""安全相关:JWT、密码、当前用户"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, Header
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import BizException, BizCode
from app.models.user import User


def create_access_token(user_id: int, is_admin: bool = False) -> str:
    """生成 JWT,V1 用 user_id + is_admin 两个 claim 就够"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "is_admin": is_admin,
        "iat": int(now.timestamp()),
        "exp": int(
            (
                now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            ).timestamp()
        ),
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as e:
        if "expired" in str(e):
            raise BizException(BizCode.TOKEN_EXPIRED, "登录已过期,请重新登录")
        raise BizException(BizCode.TOKEN_INVALID, "无效的登录态")


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI 依赖:从 Authorization: Bearer xxx 取当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise BizException(BizCode.AUTH_FAILED, "请先登录")
    token = authorization[7:]
    payload = decode_token(token)
    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id, User.status == "active").first()
    if not user:
        raise BizException(BizCode.AUTH_FAILED, "用户不存在或已禁用")
    return user


def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_admin:
        raise BizException(BizCode.NO_PERMISSION, "需要管理员权限")
    return user
