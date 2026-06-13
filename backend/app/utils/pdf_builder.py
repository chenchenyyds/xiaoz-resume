"""PDF 生成 - 模板化入口(决策 21)

决策 21: 模板系统 + 分页优化 + 字体/行距/模块间距可调
- build_pdf 接收 template_code + style_options,转发给具体模板
- 默认走 classic 模板
- 决策 20 修复(bullet 用 reportlab bulletText + Helvetica 渲染)保留在每个模板里
"""

import time
from typing import Optional, Dict, Any
from io import BytesIO
from loguru import logger

from app.utils.md_parser import parse_md
from app.utils.templates.registry import get_template
from app.utils.templates.base import StyleOptions


def build_pdf(
    md_text: str,
    template_code: str = "classic",
    style_options: Optional[Dict[str, Any]] = None,
) -> bytes:
    """把 markdown 文本转成 PDF 字节(按 template_code 渲染,style_options 调参)

    Args:
        md_text: 简历 markdown 文本
        template_code: 模板代码(classic/modern/sidebar),未知降级 classic
        style_options: {font_size, line_height, section_gap}

    Returns:
        PDF 二进制
    """
    t0 = time.time()
    options = StyleOptions.from_dict(style_options or {})
    tmpl = get_template(template_code)
    tokens = parse_md(md_text)
    logger.info(
        f"[pdf_builder] template={tmpl.name} options={options.__dict__} "
        f"tokens={len(tokens)} md_len={len(md_text or '')}"
    )
    pdf_bytes = tmpl.render_pdf(tokens, options)
    ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[pdf_builder] OK template={tmpl.name} bytes={len(pdf_bytes)} duration={ms}ms"
    )
    return pdf_bytes
