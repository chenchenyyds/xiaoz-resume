"""鉴权 API - 2 个"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BizException, BizCode
from app.core.security import create_access_token
from app.core.sms import send_sms_code, verify_sms_code
from app.core.cache import redis_client, sms_send_key, sms_code_key
from app.schemas.auth import SendSmsReq, LoginReq, LoginResp
from app.services import user_service
from app.services.config_service import get_config_int
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["鉴权"])


@router.post("/send-sms", summary="发送验证码")
async def send_sms(req: SendSmsReq, db: Session = Depends(get_db)):
    # 限频:同号 60s 内 1 次
    if redis_client.exists(sms_send_key(req.phone)):
        raise BizException(BizCode.RATE_LIMIT, "请求太频繁,请稍后再试")
    # 限频:同号每天最多 10 次
    daily_key = f"sms:daily:{req.phone}:{__import__('datetime').datetime.now().strftime('%Y%m%d')}"
    daily_count = redis_client.incr(daily_key)
    if daily_count == 1:
        redis_client.expire(daily_key, 86400)
    if daily_count > get_config_int(db, "limit.sms_per_phone_per_day", 10):
        raise BizException(BizCode.RATE_LIMIT, "今日发送次数已达上限")

    code = send_sms_code(req.phone)
    # 开发模式直接返回 code 方便测试,生产应去掉
    return {
        "code": 0,
        "message": "ok",
        "data": {"sent": True, "dev_code": code if settings.SMS_DEV_MODE else None},
    }


@router.post("/login", summary="登录/注册", response_model=dict)
async def login(req: LoginReq, db: Session = Depends(get_db)):
    if not verify_sms_code(req.phone, req.code):
        raise BizException(BizCode.AUTH_FAILED, "验证码错误或已过期")

    user, is_new = user_service.register_or_login(db, req.phone, req.invite_code)
    token = create_access_token(user.id, user.is_admin)

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "token": token,
            "user_id": user.id,
            "is_new": is_new,
            "invite_code": user.invite_code,
        },
    }
