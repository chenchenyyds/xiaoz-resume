"""改写服务：核心 LLM 调用

V1 砍掉了：
- LangGraph 循环
- 多模型路由
- 流式输出
- 用户编辑后重写

V1 保留：
- 单次 LLM 调用出结果
- 固定 prompt 模板
- 强结构化输出(JSON)
"""

import json
import re
import time
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from loguru import logger

from app.core.llm import chat, chat_json
from app.core.exceptions import BizException, BizCode
from app.models.resume import ResumeFile
from app.models.rewrite import RewriteRecord
from app.services import points_service
from app.services.config_service import get_config_int
from app.utils.docx_parser import build_docx
from app.utils.pdf_builder import build_pdf
from app.core.oss import upload_bytes


# ============================================
# Prompt 模板 - V1 锁定,后续 A/B 测试再加
# ============================================

PARTIAL_REWRITE_SYSTEM = """你是一位资深的简历优化师,擅长用 STAR 法则改写中文简历段落。
你的任务是把用户提供的简历片段改得更专业、更量化、更有冲击力。

改写要求:
1. 保留原意,不要编造事实
2. 用动词开头,避免"负责"、"参与"等弱动词
3. 尽量量化(没有数据时用百分比、用户量等)
4. 长度控制在原文的 1.2-1.5 倍
5. 用第一人称(隐含)即可,不要出现"我"字

输出 JSON 格式:
{
  "output_text": "改写后的文本",
  "explanation": "这次改了什么、为什么这样改(2-3 句话)"
}"""


FULL_REWRITE_SYSTEM = """你是一位资深的简历优化师,擅长针对中文求职简历做全面改写。
你的任务是把用户上传的简历改写得更专业、更有竞争力,符合 HR 快速阅读的习惯。

改写要求:
1. 保留所有真实信息(姓名、学校、公司、项目),只改写表达
2. 工作经历/项目经历用 STAR 法则改写
3. 技能清单按"精通/熟悉/了解"分层
4. 整体长度控制在原简历 0.8-1.2 倍
5. 用 markdown 格式输出,用 # 和 ## 分层级
6. 末尾加 5 条优化点说明

输出 JSON 格式:
{
  "output_text": "完整改写后的简历(markdown 格式)",
  "improvement_points": ["优化点1", "优化点2", "优化点3", "优化点4", "优化点5"]
}"""


FULL_REWRITE_WITH_JD_SYSTEM = """你是一位资深的求职咨询师,擅长针对特定 JD(职位描述)优化中文简历。
你的任务是把用户的简历改写成"对这份 JD 量身定制"的版本。

优化要求:
1. 保留所有真实信息,只调整表达和重点
2. 把简历中与 JD 关键词匹配的技能/经历前置和突出
3. 把不相关的经历弱化或合并
4. 工作经历/项目经历的改写要明显体现与 JD 的匹配
5. 末尾加 5 条"匹配点"说明(简历中哪些点对应 JD 哪些要求)
6. 用 markdown 格式输出

输出 JSON 格式:
{
  "output_text": "针对 JD 优化后的简历(markdown 格式)",
  "improvement_points": ["匹配点1", "匹配点2", "匹配点3", "匹配点4", "匹配点5"]
}"""


# ============================================
# 业务实现
# ============================================


def partial_rewrite(
    db: Session,
    user_id: int,
    text: str,
    title: Optional[str] = None,
    style_hint: Optional[str] = None,
) -> dict:
    """部分改写:50 积分"""
    t0 = time.time()
    cost = get_config_int(db, "points.partial_rewrite", 50)
    logger.info(
        f"[rewrite.partial] user={user_id} start cost={cost} "
        f"text_len={len(text or '')} title={title!r} style={style_hint!r}"
    )

    # 扣分
    deducted, txns = points_service.consume_points(
        db, user_id=user_id, amount=cost, feature="partial_rewrite"
    )
    txn = txns[0] if txns else None

    # 拼 user prompt
    user_prompt_parts = [f"原文:\n{text}"]
    if title:
        user_prompt_parts.append(f"\n所属板块:{title}")
    if style_hint:
        user_prompt_parts.append(f"\n风格要求:{style_hint}")
    user_prompt_parts.append("\n请按要求输出 JSON。")
    user_prompt = "\n".join(user_prompt_parts)

    # 调 LLM
    llm_t0 = time.time()
    result = chat_json(
        messages=[
            {"role": "system", "content": PARTIAL_REWRITE_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
    )
    llm_ms = int((time.time() - llm_t0) * 1000)
    parsed = result["parsed"]

    # 写记录
    record = RewriteRecord(
        user_id=user_id,
        feature="partial_rewrite",
        input_text=text,
        title=title,
        style_hint=style_hint,
        output_text=parsed.get("output_text", ""),
        points_cost=cost,
        point_transaction_id=txn.id if txn else None,
        model_name=result.get("model_name"),
        input_tokens=result.get("input_tokens"),
        output_tokens=result.get("output_tokens"),
        duration_ms=result.get("duration_ms"),
    )
    db.add(record)
    db.commit()

    # 查余额
    balance = points_service.get_balance(db, user_id)["total_balance"]

    total_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[rewrite.partial] user={user_id} OK record_id={record.id} cost={cost} "
        f"balance={balance} llm={llm_ms}ms total={total_ms}ms "
        f"in={result.get('input_tokens')} out={result.get('output_tokens')} "
        f"model={result.get('model_name')}"
    )

    return {
        "output_text": parsed.get("output_text", ""),
        "explanation": parsed.get("explanation", ""),
        "points_cost": cost,
        "points_remaining": balance,
        "record_id": record.id,
    }


def full_rewrite(
    db: Session,
    user_id: int,
    file_id: int,
    jd_text: Optional[str] = None,
    style_hint: Optional[str] = None,
) -> dict:
    """完整改写:1000 积分(含 JD 1500)"""
    t0 = time.time()
    has_jd = bool(jd_text and jd_text.strip())
    cost_key = "points.full_rewrite_with_jd" if has_jd else "points.full_rewrite"
    cost = get_config_int(db, cost_key, 1500 if has_jd else 1000)
    logger.info(
        f"[rewrite.full] user={user_id} start file_id={file_id} has_jd={has_jd} "
        f"jd_len={len(jd_text or '')} cost={cost}"
    )

    # 取简历文件
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
        raise BizException(BizCode.NOT_FOUND, "简历文件不存在或已删除")
    if rf.type == "generated":
        raise BizException(BizCode.PARAM_ERROR, "不能对生成结果再做改写,请上传新简历")
    logger.info(
        f"[rewrite.full] user={user_id} 源简历 OK file_id={rf.id} type={rf.type} chars={len(rf.content_text or '')}"
    )

    # 扣分
    deducted, txns = points_service.consume_points(
        db,
        user_id=user_id,
        amount=cost,
        feature="full_rewrite_with_jd" if has_jd else "full_rewrite",
    )
    txn = txns[0] if txns else None

    # 拼 prompt
    system = FULL_REWRITE_WITH_JD_SYSTEM if has_jd else FULL_REWRITE_SYSTEM
    user_prompt_parts = [f"简历原文:\n{rf.content_text or ''}"]
    if has_jd:
        user_prompt_parts.append(f"\n目标 JD:\n{jd_text}")
    if style_hint:
        user_prompt_parts.append(f"\n风格要求:{style_hint}")
    user_prompt_parts.append("\n请按要求输出 JSON。")
    user_prompt = "\n".join(user_prompt_parts)

    # 调 LLM
    llm_t0 = time.time()
    result = chat_json(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        max_tokens=4000,
    )
    llm_ms = int((time.time() - llm_t0) * 1000)
    parsed = result["parsed"]
    output_text = parsed.get("output_text", "")
    improvement_points = parsed.get("improvement_points", [])
    logger.info(
        f"[rewrite.full] user={user_id} LLM OK out_len={len(output_text)} "
        f"in={result.get('input_tokens')} out={result.get('output_tokens')} llm={llm_ms}ms"
    )

    # 生成 docx 和 pdf 并上传
    build_t0 = time.time()
    docx_bytes = build_docx(output_text)
    pdf_bytes = build_pdf(output_text)
    build_ms = int((time.time() - build_t0) * 1000)
    logger.info(
        f"[rewrite.full] user={user_id} 构建 OK docx={len(docx_bytes)}B pdf={len(pdf_bytes)}B build={build_ms}ms"
    )

    docx_url = upload_bytes(docx_bytes, ext="docx", prefix="resume/generated")
    pdf_url = upload_bytes(pdf_bytes, ext="pdf", prefix="resume/generated")

    # 保存生成的 docx 记录(主下载)
    gen_file = ResumeFile(
        user_id=user_id,
        type="generated",
        file_name=f"AI改写-{rf.file_name}",
        file_format="docx",
        file_url=docx_url,
        file_size=len(docx_bytes),
        content_text=output_text,
        title=rf.title,
        with_jd=has_jd,
        jd_text=jd_text,
    )
    db.add(gen_file)
    db.flush()

    # 写改写记录
    record = RewriteRecord(
        user_id=user_id,
        feature="full_rewrite_with_jd" if has_jd else "full_rewrite",
        source_file_id=rf.id,
        jd_text=jd_text,
        style_hint=style_hint,
        generated_file_id=gen_file.id,
        output_text=output_text,
        improvement_points=improvement_points,
        points_cost=cost,
        point_transaction_id=txn.id if txn else None,
        model_name=result.get("model_name"),
        input_tokens=result.get("input_tokens"),
        output_tokens=result.get("output_tokens"),
        duration_ms=result.get("duration_ms"),
    )
    db.add(record)
    db.commit()

    # 查余额
    balance = points_service.get_balance(db, user_id)["total_balance"]

    total_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[rewrite.full] user={user_id} OK record_id={record.id} file_id={gen_file.id} "
        f"cost={cost} balance={balance} llm={llm_ms}ms build={build_ms}ms total={total_ms}ms "
        f"in={result.get('input_tokens')} out={result.get('output_tokens')} model={result.get('model_name')}"
    )

    return {
        "file_id": gen_file.id,
        "output_text": output_text,
        "improvement_points": improvement_points,
        "points_cost": cost,
        "points_remaining": balance,
        "record_id": record.id,
        "file_url": docx_url,  # 主下载(docx),兼容老字段
        "docx_url": docx_url,
        "pdf_url": pdf_url,
    }
