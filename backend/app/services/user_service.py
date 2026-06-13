"""用户服务：注册、登录、生成推广码"""
import random
import string
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from loguru import logger

from app.models.user import User
from app.models.point import PointAccount, PointTransaction
from app.services import points_service
from app.services.config_service import get_config_int


def _gen_invite_code(length: int = 8) -> str:
    """8 位数字+字母推广码"""
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace("O", "").replace("I", "").replace("0", "").replace("1", "")
    return "".join(random.choices(chars, k=length))


def _gen_unique_invite_code(db: Session, length: int = 8) -> str:
    for _ in range(10):
        code = _gen_invite_code(length)
        if not db.query(User).filter(User.invite_code == code).first():
            return code
    raise RuntimeError("生成推广码失败")


def get_by_phone(db: Session, phone: str) -> Optional[User]:
    return db.query(User).filter(User.phone == phone).first()


def get_by_invite_code(db: Session, invite_code: str) -> Optional[User]:
    return db.query(User).filter(User.invite_code == invite_code).first()


def register_or_login(
    db: Session, phone: str, invite_code_from_input: Optional[str] = None
) -> tuple[User, bool]:
    """登录或注册。返回 (user, is_new)"""
    user = get_by_phone(db, phone)
    is_new = False

    if not user:
        is_new = True
        # 处理推广人
        invite_user_id = None
        if invite_code_from_input:
            inviter = get_by_invite_code(db, invite_code_from_input)
            if inviter and inviter.phone != phone:
                invite_user_id = inviter.id

        user = User(
            phone=phone,
            nickname=f"用户{phone[-4:]}",
            invite_code=_gen_unique_invite_code(db),
            invite_user_id=invite_user_id,
            status="active",
        )
        db.add(user)
        db.flush()  # 拿到 user.id

        # 注册即送试用积分
        trial_points = get_config_int(db, "trial.points", 50)
        points_service.grant_points(
            db,
            user_id=user.id,
            point_type="trial",
            amount=trial_points,
            source="trial",
            feature="register",
            remark="注册赠送",
        )

        # 给推广人发被推广奖励(给推广人加,不是给被推广人)
        if invite_user_id:
            inviter_bonus = get_config_int(db, "invitee.bonus.points", 200)
            points_service.grant_points(
                db,
                user_id=invite_user_id,
                point_type="trial",
                amount=inviter_bonus,
                source="invite_bonus",
                feature="invite",
                related_id=user.id,
                remark=f"邀请新用户 {phone[-4:]} 奖励",
            )
            logger.info(f"新用户 {phone} 由 {invite_user_id} 邀请注册")

    # 无论新老用户,都更新 last_active_at
    user.last_active_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user, is_new
