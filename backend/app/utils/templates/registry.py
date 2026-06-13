"""模板注册表 - 单例管理内置模板

使用:
    from app.utils.templates.registry import get_template
    tmpl = get_template("classic")  # 不存在会 fallback 到 classic
    pdf_bytes = tmpl.render_pdf(tokens, StyleOptions())
"""

from typing import Dict
from loguru import logger

from app.utils.templates.base import BaseTemplate, StyleOptions
from app.utils.templates.classic import ClassicTemplate
from app.utils.templates.modern import ModernTemplate
from app.utils.templates.sidebar import SidebarTemplate


_TEMPLATES: Dict[str, BaseTemplate] = {
    "classic": ClassicTemplate(),
    "modern": ModernTemplate(),
    "sidebar": SidebarTemplate(),
}


def get_template(code: str = "classic") -> BaseTemplate:
    """按 code 取模板,未知 code 降级 classic"""
    tmpl = _TEMPLATES.get(code)
    if tmpl is None:
        logger.warning(f"[template] unknown code={code!r}, fallback to classic")
        return _TEMPLATES["classic"]
    return tmpl


def list_templates() -> list:
    """列出所有内置模板(code, display_name, description)"""
    return [
        {"code": t.name, "display_name": t.display_name, "description": t.description}
        for t in _TEMPLATES.values()
    ]


__all__ = ["BaseTemplate", "StyleOptions", "get_template", "list_templates"]
