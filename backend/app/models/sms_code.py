"""短信验证码模型"""
from sqlalchemy import Column, BigInteger, Integer, String, Boolean, TIMESTAMP, func
from app.core.database import Base


class SmsCode(Base):
    __tablename__ = "sms_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), nullable=False)
    code = Column(String(6), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    expire_at = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
