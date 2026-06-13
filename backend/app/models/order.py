"""订单"""
from sqlalchemy import Column, BigInteger, Integer, String, Numeric, TIMESTAMP, func
from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(32), unique=True, nullable=False, index=True)
    user_id = Column(Integer, index=True)
    product_code = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    pay_amount = Column(Numeric(10, 2))
    pay_channel = Column(String(20))
    pay_trade_no = Column(String(64))
    status = Column(String(20), default="pending", nullable=False)
    invite_user_id = Column(Integer)
    redeem_code_id = Column(Integer)
    paid_at = Column(TIMESTAMP(timezone=True))
    refunded_at = Column(TIMESTAMP(timezone=True))
    refund_amount = Column(Numeric(10, 2))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
