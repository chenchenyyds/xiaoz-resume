"""PDF 生成 - 用 reportlab 内置 CID 字体支持中文

按 MD 解析后的 token 流渲染:
- H1/H2/H3 → 标题样式
- 列表 → bullet/number 缩进
- 段落内 **加粗** / `行内代码` → 用 reportlab Paragraph 内联标签
- > 引用 → 斜体 + 灰色
"""
import time
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from loguru import logger

from app.utils.md_parser import parse_md, render_runs_to_html

# 注册内置 CID 中文字体(只注册一次)
try:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    CN_FONT = "STSong-Light"
except Exception as e:
    logger.warning(f"注册 STSong-Light 失败,降级到 STSongStd-Light: {e}")
    pdfmetrics.registerFont(UnicodeCIDFont("STSongStd-Light"))
    CN_FONT = "STSongStd-Light"


def _build_styles():
    """构造简历用的样式集"""
    base = getSampleStyleSheet()["Normal"]
    title_style = ParagraphStyle(
        "Title", parent=base, fontName=CN_FONT, fontSize=18, leading=26,
        spaceBefore=10, spaceAfter=10, alignment=TA_LEFT,
        textColor="#1a1a1a",
    )
    h2_style = ParagraphStyle(
        "H2", parent=base, fontName=CN_FONT, fontSize=13, leading=20,
        spaceBefore=10, spaceAfter=5, textColor="#2a2a2a",
        borderPadding=2,
    )
    h3_style = ParagraphStyle(
        "H3", parent=base, fontName=CN_FONT, fontSize=11.5, leading=17,
        spaceBefore=6, spaceAfter=3, textColor="#333333",
    )
    body_style = ParagraphStyle(
        "Body", parent=base, fontName=CN_FONT, fontSize=10.5, leading=17,
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=body_style, leftIndent=14, bulletIndent=2,
        spaceAfter=2,
    )
    bullet2_style = ParagraphStyle(
        "Bullet2", parent=bullet_style, leftIndent=30,
    )
    quote_style = ParagraphStyle(
        "Quote", parent=body_style, leftIndent=20, fontSize=10,
        textColor="#666666", fontName=CN_FONT,
    )
    return title_style, h2_style, h3_style, body_style, bullet_style, bullet2_style, quote_style


def build_pdf(md_text: str) -> bytes:
    """把 markdown 文本转成 PDF 字节(按 MD 解析后的 tokens 渲染)"""
    t0 = time.time()
    title_style, h2_style, h3_style, body_style, bullet_style, bullet2_style, quote_style = _build_styles()

    # 解析 MD
    tokens = parse_md(md_text)
    logger.info(f"[pdf_builder] parsed {len(tokens)} tokens from md len={len(md_text or '')}")

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="AI 改写简历",
    )

    story = []
    h1 = h2 = h3 = p_cnt = ul_cnt = ol_cnt = quote_cnt = 0

    for tok in tokens:
        t = tok['type']
        if t == 'h1':
            content = _escape(tok['content'])
            story.append(Paragraph(content, title_style))
            h1 += 1
        elif t == 'h2':
            content = _escape(tok['content'])
            story.append(Paragraph(content, h2_style))
            h2 += 1
        elif t == 'h3':
            content = _escape(tok['content'])
            story.append(Paragraph(content, h3_style))
            h3 += 1
        elif t == 'p':
            inline_html = render_runs_to_html(tok['runs'])
            if inline_html.strip():
                story.append(Paragraph(inline_html, body_style))
                p_cnt += 1
        elif t in ('ul', 'ol'):
            for idx, item in enumerate(tok['items']):
                inline_html = render_runs_to_html(item['runs'])
                if not inline_html.strip():
                    continue
                # 检测嵌套 level
                level = 0
                if item['runs'] and 'level' in item['runs'][0]:
                    level = item['runs'][0]['level'] or 0
                style = bullet2_style if level > 0 else bullet_style
                if t == 'ul':
                    bullet = "• " if level == 0 else "◦ "
                    story.append(Paragraph(f"{bullet}{inline_html}", style))
                else:
                    story.append(Paragraph(f"{idx + 1}. {inline_html}", style))
                if t == 'ul':
                    ul_cnt += 1
                else:
                    ol_cnt += 1
        elif t == 'blockquote':
            content = _escape(tok['content'])
            story.append(Paragraph(f"│ {content}", quote_style))
            quote_cnt += 1

    doc.build(story)
    pdf_bytes = buf.getvalue()
    ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[pdf_builder] OK bytes={len(pdf_bytes)} h1={h1} h2={h2} h3={h3} "
        f"p={p_cnt} ul={ul_cnt} ol={ol_cnt} quote={quote_cnt} "
        f"duration={ms}ms font={CN_FONT}"
    )
    return pdf_bytes


def _escape(text: str) -> str:
    """转义 reportlab Paragraph 的特殊字符"""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )
