"""简历文件"""

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Integer,
    Boolean,
    Text,
    JSON,
    TIMESTAMP,
    func,
)
from app.core.database import Base


class ResumeFile(Base):
    __tablename__ = "resume_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    type = Column(String(20), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_format = Column(String(20), nullable=False)
    file_url = Column(String(512))
    file_size = Column(Integer)
    content_text = Column(Text)
    content_json = Column(JSON)
    title = Column(String(255))
    with_jd = Column(Boolean, default=False)
    jd_text = Column(Text)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
