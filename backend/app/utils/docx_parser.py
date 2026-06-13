"""docx 解析/生成 - 模板化入口(决策 21)

决策 21: 模板系统
- build_docx 接收 template_code + style_options,转发给具体模板
- 默认走 classic 模板
- 决策 20 修复(docx Heading 样式 + List Bullet 样式)保留在每个模板里
"""

import time
from io import BytesIO
from typing import Optional, Dict, Any
from docx import Document
from loguru import logger

from app.utils.md_parser import parse_md
from app.utils.templates.registry import get_template
from app.utils.templates.base import StyleOptions


def parse_docx(content: bytes) -> dict:
    """解析 docx 字节,返回 {text, paragraphs, sections}

    简化处理:把每段当一段,不做结构化(姓名/教育/工作分开)
    V1 改写是基于全文的,不做结构化也够用
    """
    try:
        doc = Document(BytesIO(content))
    except Exception as e:
        logger.exception("docx 解析失败")
        raise ValueError(f"docx 文件无法解析: {e}")

    paragraphs = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            paragraphs.append(text)

    full_text = "\n".join(paragraphs)
    return {
        "text": full_text,
        "paragraphs": paragraphs,
        "sections": [],
        "char_count": len(full_text),
    }


def build_docx(
    md_text: str,
    template_code: str = "classic",
    style_options: Optional[Dict[str, Any]] = None,
) -> bytes:
    """把 MD 转成结构化 docx 字节(按 template_code 渲染,style_options 调参)

    Args:
        md_text: 简历 markdown 文本
        template_code: 模板代码(classic/modern/sidebar),未知降级 classic
        style_options: {font_size, line_height, section_gap}
    """
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    t0 = time.time()
    options = StyleOptions.from_dict(style_options or {})
    tmpl = get_template(template_code)

    # 解析 MD
    tokens = parse_md(md_text)
    logger.info(
        f"[docx_builder] template={tmpl.name} options={options.__dict__} "
        f"tokens={len(tokens)} md_len={len(md_text or '')}"
    )

    # 新建空 doc
    doc = Document()
    _setup_default_style(doc)

    # 委托给模板渲染
    tmpl.render_docx(doc, tokens, options)

    # 页脚
    footer = doc.sections[0].footer
    p = footer.paragraphs[0]
    p.text = "本简历由 AI 辅助生成,求职者应自行核实真实性"

    buf = BytesIO()
    doc.save(buf)
    bytes_out = buf.getvalue()
    ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[docx_builder] OK template={tmpl.name} bytes={len(bytes_out)} duration={ms}ms"
    )
    return bytes_out


def _setup_default_style(doc) -> None:
    """设置 Normal 样式:中文微软雅黑,英文 Calibri"""
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    from docx.shared import Pt as _Pt

    style.font.size = _Pt(10.5)
    rpr = style.element.rPr
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    rfonts.set(qn("w:ascii"), "Calibri")
    rfonts.set(qn("w:hAnsi"), "Calibri")
