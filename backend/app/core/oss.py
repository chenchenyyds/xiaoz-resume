"""阿里云 OSS 文件上传 - 简历文件"""
import os
import uuid
from datetime import datetime
from typing import Optional
import oss2
from loguru import logger

from app.core.config import settings


def _bucket() -> oss2.Bucket:
    auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
    return oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET)


def upload_bytes(content: bytes, ext: str = "docx", prefix: str = "resume") -> str:
    """上传字节,返回 OSS URL"""
    if not settings.OSS_ACCESS_KEY_ID:
        # 开发模式:无 OSS 配置时返回空(调用方应兜底)
        logger.warning("OSS 未配置,跳过上传")
        return ""

    date_path = datetime.now().strftime("%Y/%m/%d")
    obj_name = f"{prefix}/{date_path}/{uuid.uuid4().hex}.{ext}"
    bucket = _bucket()
    bucket.put_object(obj_name, content)
    return f"{settings.OSS_BASE_URL.rstrip('/')}/{obj_name}"


def upload_file(local_path: str, ext: str = "docx", prefix: str = "resume") -> str:
    """上传本地文件,返回 OSS URL"""
    if not os.path.exists(local_path):
        raise FileNotFoundError(local_path)
    with open(local_path, "rb") as f:
        return upload_bytes(f.read(), ext=ext, prefix=prefix)
