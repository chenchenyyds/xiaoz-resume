"""用户模型"""
from sqlalchemy import Column, BigInteger, Integer, String, Boolean, TIMESTAMP, func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    nickname = Column(String(50))
    avatar_url = Column(String(512))
    invite_code = Column(String(16), unique=True)
    invite_user_id = Column(Integer, index=True)
    status = Column(String(20), default="active", nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    last_active_at = Column(TIMESTAMP(timezone=True))
