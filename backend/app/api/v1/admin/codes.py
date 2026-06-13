"""后台 - 兑换码 4 个 API"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import csv

from app.core.database import get_db
from app.core.security import get_current_admin
from app.services import admin_service, redeem_service
from app.schemas.redeem import (
    GenerateCodeReq,
    GenerateCodeResp,
    CodeListResp,
    CodeListItem,
)
from app.schemas.admin import AdminCodeListResp

router = APIRouter(prefix="/codes", tags=["后台-兑换码"])


@router.post("/generate", summary="批量生成", response_model=GenerateCodeResp)
async def generate(
    req: GenerateCodeReq,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    result = redeem_service.generate_batch(
        db, req.type, req.count, req.valid_days, req.batch_id
    )
    return GenerateCodeResp(**result)


@router.get("", summary="兑换码列表", response_model=CodeListResp)
async def list_codes(
    batch_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    items, total = admin_service.list_codes(db, batch_id, status, type, page, page_size)
    return CodeListResp(
        items=[
            CodeListItem(
                id=c.id,
                code_mask=c.code_mask,
                type=c.type,
                points=c.points,
                status=c.status,
                batch_id=c.batch_id,
                user_id=c.user_id,
                used_at=c.used_at,
                created_at=c.created_at,
            )
            for c in items
        ],
        total=total,
    )


@router.post("/{code_id}/revoke", summary="作废兑换码")
async def revoke(
    code_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return redeem_service.revoke_code(db, code_id)


@router.get("/export", summary="导出 CSV")
async def export(
    batch_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    """V1 简化:CSV 只导出当前过滤条件下的所有码(明文),仅 batch_id 必有"""
    if not batch_id:
        from app.core.exceptions import BizException, BizCode

        raise BizException(BizCode.PARAM_ERROR, "导出必须指定 batch_id")

    # 找 batch 的原始明文:从历史生成响应里取,这里退化到导 code_mask
    # V1 简化版:用 code_hash 反查不现实,提示用户用 /generate 返回的明文即可
    # 这里退而求其次:导出 code_mask + 类型 + 状态,用于运营核对
    items, _ = admin_service.list_codes(
        db, batch_id=batch_id, status=status, type_=type, page=1, page_size=10000
    )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["code_mask", "type", "points", "status", "user_id", "used_at", "created_at"]
    )
    for c in items:
        writer.writerow(
            [
                c.code_mask,
                c.type,
                c.points,
                c.status,
                c.user_id or "",
                c.used_at or "",
                c.created_at,
            ]
        )

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=redeem_{batch_id}.csv"},
    )
