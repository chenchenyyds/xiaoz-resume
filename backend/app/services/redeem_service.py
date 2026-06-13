"""兑换码服务：生成(后台)、激活(用户端)、作废"""

import hashlib
import random
import string
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from loguru import logger

from app.core.exceptions import BizException, BizCode
from app.models.redeem import RedeemCode
from app.models.user import User
from app.services import points_service
from app.services.config_service import get_config_int, get_config


# 字符集(去除易混字符)
CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _gen_code(length: int = 12) -> str:
    """生成形如 XXXX-XXXX-XXXX 的兑换码"""
    raw = "".join(random.choices(CODE_CHARS, k=length))
    return f"{raw[:4]}-{raw[4:8]}-{raw[8:]}"


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _mask_code(code: str) -> str:
    """脱敏:前 4 后 4"""
    if len(code) < 8:
        return code[:2] + "***" + code[-2:]
    return code[:4] + "-****-" + code[-4:]


def generate_batch(
    db: Session,
    code_type: str,
    count: int,
    valid_days: int = 365,
    batch_id: Optional[str] = None,
) -> dict:
    """后台批量生成兑换码

    V1 简化:每种类型对应固定的积分数量(从 system_configs 读)
    """
    type_points_map = {
        "single": "product.single.points",
        "monthly": "product.monthly.points",
        "points_1000": "product.points_1000.points",
        "trial": "trial.points",
    }
    points_key = type_points_map.get(code_type)
    if not points_key:
        raise BizException(BizCode.PARAM_ERROR, f"不支持的兑换码类型 {code_type}")

    points = get_config_int(db, points_key, 0)
    if points <= 0:
        raise BizException(BizCode.PARAM_ERROR, f"类型 {code_type} 未配置积分")

    batch_id = (
        batch_id
        or f"B{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
    )
    expire_at = datetime.now(timezone.utc) + timedelta(days=valid_days)
    codes_plain = []
    codes_db = []

    for _ in range(count):
        for _attempt in range(5):
            code = _gen_code()
            code_hash = _hash_code(code)
            if (
                not db.query(RedeemCode)
                .filter(RedeemCode.code_hash == code_hash)
                .first()
            ):
                break
        else:
            raise RuntimeError("生成兑换码失败,重试 5 次仍冲突")

        codes_plain.append(code)
        codes_db.append(
            RedeemCode(
                code_hash=_hash_code(code),
                code_mask=_mask_code(code),
                type=code_type,
                points=points,
                status="unused",
                batch_id=batch_id,
                expire_at=expire_at,
            )
        )

    db.add_all(codes_db)
    db.commit()
    logger.info(f"生成兑换码 {count} 个 type={code_type} batch={batch_id}")
    return {
        "batch_id": batch_id,
        "count": count,
        "codes": codes_plain,  # 明文,只这次返回,务必提示用户保存
    }


def activate_code(db: Session, user_id: int, code: str) -> dict:
    """用户端激活兑换码"""
    code = code.strip().upper()
    code_hash = _hash_code(code)

    rc = db.query(RedeemCode).filter(RedeemCode.code_hash == code_hash).first()
    if not rc:
        raise BizException(BizCode.NOT_FOUND, "兑换码不存在")

    if rc.status == "used":
        raise BizException(BizCode.CONFLICT, "兑换码已被使用")
    if rc.status == "revoked":
        raise BizException(BizCode.CONFLICT, "兑换码已作废")
    # 兼容 SQLite naive UTC: 写入时 SQLAlchemy 会自动 strip tz,读出来是 naive
    if rc.expire_at and rc.expire_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise BizException(BizCode.CONFLICT, "兑换码已过期")

    # 标记为已使用
    rc.status = "used"
    rc.user_id = user_id
    rc.used_at = datetime.now(timezone.utc)

    # 加积分(兑换码一般是订阅类型,30 天有效)
    if rc.type == "trial":
        point_type = "trial"
        valid_days = 90
    elif rc.type in ("single", "monthly"):
        point_type = "subscription"
        valid_days = 30
    else:  # points_1000
        point_type = "purchase"
        valid_days = 0  # 永久

    expire_at = (
        datetime.now(timezone.utc) + timedelta(days=valid_days)
        if valid_days > 0
        else None
    )

    points_service.grant_points(
        db,
        user_id=user_id,
        point_type=point_type,
        amount=rc.points,
        source="redeem",
        feature=rc.type,
        related_id=rc.id,
        remark=f"兑换码 {rc.code_mask} 激活",
        expire_at=expire_at,
    )
    db.commit()

    balance = points_service.get_balance(db, user_id)["total_balance"]
    logger.info(f"用户 {user_id} 激活兑换码 {rc.code_mask},获得 {rc.points} 积分")
    return {
        "type": rc.type,
        "points": rc.points,
        "valid_days": valid_days,
        "points_balance": balance,
    }


def revoke_code(db: Session, code_id: int):
    """后台作废兑换码"""
    rc = db.query(RedeemCode).filter(RedeemCode.id == code_id).first()
    if not rc:
        raise BizException(BizCode.NOT_FOUND, "兑换码不存在")
    if rc.status == "used":
        raise BizException(BizCode.CONFLICT, "已使用的兑换码不可作废")
    rc.status = "revoked"
    db.commit()
    return {"id": code_id, "status": "revoked"}
