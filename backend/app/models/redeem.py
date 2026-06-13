"""兑换码"""

from sqlalchemy import Column, BigInteger, String, Integer, TIMESTAMP, func
from app.core.database import Base


class RedeemCode(Base):
    __tablename__ = "redeem_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_hash = Column(String(64), unique=True, nullable=False, index=True)
    code_mask = Column(String(32), nullable=False)
    type = Column(String(20), nullable=False)
    points = Column(Integer, nullable=False)
    status = Column(String(20), default="unused", nullable=False)
    batch_id = Column(String(32), index=True)
    order_id = Column(Integer)
    user_id = Column(Integer)
    used_at = Column(TIMESTAMP(timezone=True))
    expire_at = Column(TIMESTAMP(timezone=True))
    invite_user_id = Column(Integer)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
