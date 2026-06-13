"""文件服务:上传 docx/pdf、解析、存 OSS"""

import os
import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile
from loguru import logger

from app.core.exceptions import BizException, BizCode
from app.core.oss import upload_bytes
from app.models.resume import ResumeFile
from app.services.config_service import get_config_int
from app.utils.docx_parser import parse_docx
from app.utils.pdf_parser import parse_pdf


ALLOWED_FORMATS = {"docx", "pdf"}
PARSERS = {
    "docx": parse_docx,
    "pdf": parse_pdf,
}


def _validate(file: UploadFile, max_size_mb: int):
    """校验文件格式和大小"""
    # 扩展名
    if not file.filename:
        raise BizException(BizCode.PARAM_ERROR, "文件名不能为空")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_FORMATS:
        raise BizException(
            BizCode.PARAM_ERROR, f"仅支持 {','.join(ALLOWED_FORMATS)} 格式"
        )
    # 大小
    file.file.seek(0, 2)  # 移到末尾
    size = file.file.tell()
    file.file.seek(0)  # 复位
    if size > max_size_mb * 1024 * 1024:
        raise BizException(BizCode.PARAM_ERROR, f"文件超过 {max_size_mb}MB 限制")
    return ext, size


async def save_uploaded_resume(
    db: Session,
    user_id: int,
    file: UploadFile,
    title: Optional[str] = None,
) -> dict:
    """保存用户上传的简历"""
    t0 = time.time()
    max_mb = get_config_int(db, "file.max_size_mb", 10)
    ext, size = _validate(file, max_mb)
    logger.info(
        f"[file.upload] user={user_id} start file={file.filename} ext={ext} size={size}B max={max_mb}MB"
    )

    content = await file.read()
    if not content:
        raise BizException(BizCode.PARAM_ERROR, "文件为空")

    # 解析(根据扩展名选 parser)
    parser = PARSERS.get(ext)
    if not parser:
        raise BizException(BizCode.PARAM_ERROR, f"暂不支持 {ext} 格式")
    try:
        parsed = parser(content)
    except ValueError as e:
        logger.warning(f"[file.upload] user={user_id} 解析失败 ext={ext} err={e}")
        raise BizException(BizCode.PARAM_ERROR, str(e))

    if parsed["char_count"] < 20:
        logger.warning(
            f"[file.upload] user={user_id} 简历过短 chars={parsed['char_count']}"
        )
        raise BizException(BizCode.PARAM_ERROR, "简历内容太短,至少 20 字")

    # 上传 OSS
    file_url = upload_bytes(content, ext=ext, prefix="resume/uploaded")

    # 入库
    rf = ResumeFile(
        user_id=user_id,
        type="uploaded",
        file_name=file.filename,
        file_format=ext,
        file_url=file_url,
        file_size=size,
        content_text=parsed["text"],
        content_json={"paragraphs": parsed["paragraphs"]},
        title=title,
    )
    db.add(rf)
    db.commit()
    db.refresh(rf)

    duration_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[file.upload] user={user_id} OK file_id={rf.id} ext={ext} size={size}B "
        f"chars={parsed['char_count']} oss={'yes' if file_url else 'no'} duration={duration_ms}ms"
    )

    preview = parsed["text"][:200]
    return {
        "id": rf.id,
        "file_name": rf.file_name,
        "file_size": rf.file_size,
        "file_url": rf.file_url,
        "text_preview": preview,
    }


def list_user_files(db: Session, user_id: int, include_deleted: bool = False) -> list:
    q = db.query(ResumeFile).filter(ResumeFile.user_id == user_id)
    if not include_deleted:
        q = q.filter(ResumeFile.is_deleted == False)
    return q.order_by(ResumeFile.created_at.desc()).all()


def soft_delete_file(db: Session, user_id: int, file_id: int):
    rf = (
        db.query(ResumeFile)
        .filter(
            ResumeFile.id == file_id,
            ResumeFile.user_id == user_id,
        )
        .first()
    )
    if not rf:
        raise BizException(BizCode.NOT_FOUND, "文件不存在")
    rf.is_deleted = True
    db.commit()
    return {"id": file_id, "deleted": True}


def get_file_for_download(
    db: Session, user_id: int, file_id: int, format: str = "docx"
):
    """取文件用于下载(本地兜底,OSS 没配时也用这个)

    生成的简历(content_text 已存)按 format 实时重新生成字节流。
    上传的原始文件(file_url 有)直接返回 file_url。
    """
    t0 = time.time()
    rf = (
        db.query(ResumeFile)
        .filter(
            ResumeFile.id == file_id,
            ResumeFile.user_id == user_id,
            ResumeFile.is_deleted == False,
        )
        .first()
    )
    if not rf:
        raise BizException(BizCode.NOT_FOUND, "文件不存在或已删除")
    logger.info(
        f"[file.download] user={user_id} file_id={file_id} type={rf.type} format={format} start"
    )

    # 上传的原始文件:file_url 可能是 OSS 链接(浏览器直下)或空(本地兜底)
    if rf.type == "uploaded":
        kind = "url" if rf.file_url else "lost"
        duration_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"[file.download] user={user_id} file_id={file_id} kind={kind} duration={duration_ms}ms"
        )
        return {
            "kind": "url" if rf.file_url else "lost",
            "url": rf.file_url,
            "file_name": rf.file_name,
            "format": rf.file_format,
        }

    # 生成的简历:实时重建字节流
    if not rf.content_text:
        logger.warning(
            f"[file.download] user={user_id} file_id={file_id} content_text 丢失"
        )
        raise BizException(BizCode.NOT_FOUND, "文件内容已丢失")

    fmt = (format or "docx").lower()
    if fmt == "pdf":
        from app.utils.pdf_builder import build_pdf

        data = build_pdf(rf.content_text)
        media = "application/pdf"
    else:
        from app.utils.docx_parser import build_docx

        data = build_docx(rf.content_text)
        media = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        fmt = "docx"

    base_name = (rf.file_name or "resume").rsplit(".", 1)[0]
    # 文件名转 ASCII-safe(下载头 latin-1 限制),保 slug 化文件名
    import re as _re

    safe_base = _re.sub(r"[^A-Za-z0-9_-]+", "_", base_name).strip("_") or "resume"
    download_name = f"{safe_base}.{fmt}"
    duration_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[file.download] user={user_id} file_id={file_id} kind=bytes fmt={fmt} "
        f"bytes={len(data)} duration={duration_ms}ms"
    )
    return {
        "kind": "bytes",
        "data": data,
        "file_name": download_name,
        "media": media,
    }
