"""积分账户 + 流水"""
from sqlalchemy import Column, BigInteger, String, Integer, Text, TIMESTAMP, ForeignKey, func
from app.core.database import Base


class PointAccount(Base):
    __tablename__ = "point_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    point_type = Column(String(20), nullable=False)  # trial/subscription/purchase
    balance = Column(Integer, default=0, nullable=False)
    total_earned = Column(Integer, default=0, nullable=False)
    total_used = Column(Integer, default=0, nullable=False)
    expire_at = Column(TIMESTAMP(timezone=True))
    source = Column(String(50))
    related_id = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class PointTransaction(Base):
    __tablename__ = "point_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    point_type = Column(String(20), nullable=False)
    change = Column(Integer, nullable=False)
    balance_before = Column(Integer)
    balance_after = Column(Integer)
    source = Column(String(50))
    related_id = Column(Integer)
    feature = Column(String(50))
    remark = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
