"""系统配置"""
from sqlalchemy import Column, String, Text, TIMESTAMP, func
from app.core.database import Base


class SystemConfig(Base):
    __tablename__ = "system_configs"

    config_key = Column(String(100), primary_key=True)
    config_value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
