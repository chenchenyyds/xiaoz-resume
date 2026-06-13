"""文件相关 schema"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FileItem(BaseModel):
    id: int
    file_name: str
    file_format: str
    file_url: Optional[str]
    file_size: Optional[int]
    type: str  # uploaded/generated
    with_jd: bool
    created_at: datetime

    class Config:
        from_attributes = True


class FileListResp(BaseModel):
    items: list[FileItem]
    total: int


class UploadResp(BaseModel):
    id: int
    file_name: str
    file_size: int
    file_url: str
    text_preview: Optional[str] = None  # 前 200 字预览
