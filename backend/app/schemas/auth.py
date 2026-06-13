"""鉴权相关 schema"""
from pydantic import BaseModel, Field, validator
import re


PHONE_RE = re.compile(r"^1[3-9]\d{9}$")


class SendSmsReq(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11)

    @validator("phone")
    def _v_phone(cls, v):
        if not PHONE_RE.match(v):
            raise ValueError("手机号格式错误")
        return v


class LoginReq(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11)
    code: str = Field(..., min_length=4, max_length=6)
    invite_code: str = Field(default=None, max_length=16)  # 可选,带推广码注册

    @validator("phone")
    def _v_phone(cls, v):
        if not PHONE_RE.match(v):
            raise ValueError("手机号格式错误")
        return v


class LoginResp(BaseModel):
    token: str
    user_id: int
    is_new: bool
    invite_code: str  # 用户自己的推广码
