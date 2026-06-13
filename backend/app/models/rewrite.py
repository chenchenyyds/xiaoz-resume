"""改写记录"""
from sqlalchemy import Column, BigInteger, String, Integer, Text, JSON, TIMESTAMP, func
from app.core.database import Base


class RewriteRecord(Base):
    __tablename__ = "rewrite_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    feature = Column(String(50), nullable=False)
    source_file_id = Column(Integer)
    input_text = Column(Text)
    jd_text = Column(Text)
    title = Column(String(50))
    style_hint = Column(String(100))
    generated_file_id = Column(Integer)
    output_text = Column(Text)
    improvement_points = Column(JSON)
    points_cost = Column(Integer, nullable=False)
    point_transaction_id = Column(Integer)
    model_name = Column(String(50))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    duration_ms = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
