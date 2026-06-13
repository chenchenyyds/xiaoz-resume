"""文件 API - 4 个"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import BizException, BizCode, ok
from app.core.rate_limit import check_rate_limit
from app.models.user import User
from app.services import file_service
from app.services.config_service import get_config_int
from app.schemas.file import FileListResp, FileItem, UploadResp

router = APIRouter(prefix="/files", tags=["文件"])


@router.post("/upload", summary="上传简历(docx/pdf)")
async def upload(
    file: UploadFile = File(...),
    title: str = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 限频:每日上传次数
    max_per_day = get_config_int(db, "limit.upload_per_day", 20)
    check_rate_limit(user.id, "upload", max_per_day, 86400)

    logger.info(
        f"[api.files.upload] user={user.id} enter filename={file.filename!r} content_type={file.content_type} title={title!r}"
    )
    result = await file_service.save_uploaded_resume(db, user.id, file, title)
    # 统一包装:与项目其它 API 一致 {code:0, message:"ok", data:...}
    return ok(UploadResp(**result).model_dump())


@router.get("", summary="我的文件列表", response_model=FileListResp)
async def list_files(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    files = file_service.list_user_files(db, user.id)
    return FileListResp(
        items=[
            FileItem(
                id=f.id,
                file_name=f.file_name,
                file_format=f.file_format,
                file_url=f.file_url,
                file_size=f.file_size,
                type=f.type,
                with_jd=f.with_jd,
                created_at=f.created_at,
            )
            for f in files
        ],
        total=len(files),
    )


@router.get("/{file_id}/download", summary="下载文件(docx/pdf)")
async def download_file(
    file_id: int,
    format: str = Query(default="docx", pattern="^(docx|pdf)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """下载文件:
    - 生成的简历:实时重建字节流(format=docx 或 pdf)
    - 上传的原始文件:file_url 有 OSS 链接则 302,否则返回 content_text 重建
    """
    logger.info(
        f"[api.files.download] user={user.id} file_id={file_id} format={format}"
    )
    res = file_service.get_file_for_download(db, user.id, file_id, format)
    if res["kind"] == "url" and res["url"]:
        # OSS 链接:重定向
        from fastapi.responses import RedirectResponse

        return RedirectResponse(res["url"])
    if res["kind"] == "url" and not res["url"]:
        # 没 OSS:从 content_text 重建(只支持 docx)
        raise BizException(BizCode.NOT_FOUND, "原文件已丢失,无法下载")
    # bytes
    return Response(
        content=res["data"],
        media_type=res["media"],
        headers={
            "Content-Disposition": f'attachment; filename="{res["file_name"]}"',
        },
    )


@router.delete("/{file_id}", summary="删除文件")
async def delete_file(
    file_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return file_service.soft_delete_file(db, user.id, file_id)
