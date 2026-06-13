"""阿里云短信发送 - V1 一家就够"""

import random
import string
from typing import Optional
from loguru import logger

from app.core.config import settings
from app.core.cache import redis_client, sms_send_key, sms_code_key
from app.core.exceptions import BizException, BizCode


def _gen_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def send_sms_code(phone: str) -> str:
    """发送短信验证码。

    开发模式(SMS_DEV_MODE=true):固定返回 123456,不真发。
    生产模式:调阿里云短信,验证码存 redis(5 分钟有效)。
    """
    if settings.SMS_DEV_MODE:
        # 开发模式固定 123456
        redis_client.setex(sms_code_key(phone), 300, "123456")
        redis_client.setex(sms_send_key(phone), 60, "1")
        logger.info(f"[DEV SMS] phone={phone} code=123456")
        return "123456"

    # ---- 真实发送 ----
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.request import CommonRequest
    import json

    code = _gen_code()
    try:
        client = AcsClient(
            settings.SMS_ACCESS_KEY_ID,
            settings.SMS_ACCESS_KEY_SECRET,
            settings.SMS_REGION,
        )
        request = CommonRequest()
        request.set_accept_format("json")
        request.set_domain("dysmsapi.aliyuncs.com")
        request.set_method("POST")
        request.set_protocol_type("https")
        request.set_version("2017-05-25")
        request.set_action_name("SendSms")
        request.add_query_param("PhoneNumbers", phone)
        request.add_query_param("SignName", settings.SMS_SIGN_NAME)
        request.add_query_param("TemplateCode", settings.SMS_TEMPLATE_CODE)
        request.add_query_param("TemplateParam", json.dumps({"code": code}))

        response = client.do_action_with_exception(request)
        result = json.loads(response)
        if result.get("Code") != "OK":
            logger.error(f"短信发送失败: {result}")
            raise BizException(
                BizCode.SMS_ERROR, f"短信发送失败: {result.get('Message', '未知错误')}"
            )

        redis_client.setex(sms_code_key(phone), 300, code)
        redis_client.setex(sms_send_key(phone), 60, "1")
        logger.info(f"短信已发送 phone={phone}")
        return code
    except BizException:
        raise
    except Exception as e:
        logger.exception("短信异常")
        raise BizException(BizCode.SMS_ERROR, f"短信服务异常: {str(e)[:100]}")


def verify_sms_code(phone: str, code: str) -> bool:
    """校验验证码,正确则删除(开发模式:不删,避免重复登录失败)"""
    if settings.SMS_DEV_MODE:
        # 开发模式:接受 123456,不消费 redis 验证码(允许重复登录)
        if code == "123456":
            # 顺手把验证码续期到 5 分钟
            redis_client.setex(sms_code_key(phone), 300, "123456")
            return True
        return False
    real = redis_client.get(sms_code_key(phone))
    if not real or real != code:
        return False
    redis_client.delete(sms_code_key(phone))
    return True
