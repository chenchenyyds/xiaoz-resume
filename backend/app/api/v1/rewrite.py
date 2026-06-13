"""改写 API - 2 个(部分改写 + 完整改写)"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import BizException, BizCode, ok
from app.core.rate_limit import check_rate_limit
from app.models.user import User
from app.services import rewrite_service
from app.services.config_service import get_config_int
from app.schemas.rewrite import (
    PartialRewriteReq,
    FullRewriteReq,
    PartialRewriteResp,
    FullRewriteResp,
    TemplateListResp,
)
from app.utils.templates.registry import list_templates

router = APIRouter(prefix="/rewrite", tags=["改写"])


@router.post("/partial", summary="部分改写(50 积分)")
async def partial_rewrite(
    req: PartialRewriteReq,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"[api.rewrite.partial] user={user.id} enter text_len={len(req.text or '')} title={req.title!r} template={req.template_code!r}"
    )
    max_per_hour = get_config_int(db, "limit.partial_per_hour", 10)
    check_rate_limit(user.id, "partial_rewrite", max_per_hour, 3600)
    return ok(
        rewrite_service.partial_rewrite(
            db,
            user.id,
            req.text,
            req.title,
            req.style_hint,
            template_code=req.template_code,
            style_options=req.style_options,
        )
    )


@router.post("/full", summary="完整改写(1000 积分/含 JD 1500)")
async def full_rewrite(
    req: FullRewriteReq,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"[api.rewrite.full] user={user.id} enter file_id={req.file_id} has_jd={bool(req.jd_text)} jd_len={len(req.jd_text or '')} template={req.template_code!r}"
    )
    max_per_hour = get_config_int(db, "limit.full_per_hour", 3)
    check_rate_limit(user.id, "full_rewrite", max_per_hour, 3600)
    return ok(
        rewrite_service.full_rewrite(
            db,
            user.id,
            req.file_id,
            req.jd_text,
            req.style_hint,
            template_code=req.template_code,
            style_options=req.style_options,
        )
    )


@router.get("/templates", summary="获取简历模板列表")
async def get_templates(db: Session = Depends(get_db)):
    """返回内置的简历模板列表(决策 21)"""
    return ok({"templates": list_templates()})
