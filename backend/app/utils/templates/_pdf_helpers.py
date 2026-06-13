"""模板系统共享辅助函数"""

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from loguru import logger

from app.utils.md_parser import render_runs_to_html


_CN_FONT_REGISTERED = False
CN_FONT = "STSong-Light"


def register_cn_font() -> str:
    """注册 CID 中文字体(全局只注册一次)"""
    global _CN_FONT_REGISTERED, CN_FONT
    if _CN_FONT_REGISTERED:
        return CN_FONT
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        CN_FONT = "STSong-Light"
    except Exception as e:
        logger.warning(f"注册 STSong-Light 失败,降级到 STSongStd-Light: {e}")
        pdfmetrics.registerFont(UnicodeCIDFont("STSongStd-Light"))
        CN_FONT = "STSongStd-Light"
    _CN_FONT_REGISTERED = True
    return CN_FONT


def escape_text(text: str) -> str:
    """转义 reportlab Paragraph 的特殊字符"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_runs_html(runs: list) -> str:
    """把 token 的 runs 列表转成 reportlab Paragraph 内联 HTML"""
    return render_runs_to_html(runs)
