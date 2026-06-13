"""模板基类 - 简历 PDF/DOCX 样式抽象接口

子类必须实现:
- name: 模板代码(英文)
- display_name: 模板中文名
- description: 模板描述
- render_pdf(tokens, style_options) -> bytes
- render_docx(doc, tokens, style_options) -> None

样式参数:
- font_size: 基础字号(pt), 范围 9-13, 默认 10.5
- line_height: 行距倍数, 范围 1.2-2.0, 默认 1.6
- section_gap: 模块间距倍数, 范围 0.5-2.0, 默认 1.0
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from docx import Document


class StyleOptions:
    """样式参数(API 入参,带范围校验)"""

    def __init__(
        self,
        font_size: float = 10.5,
        line_height: float = 1.6,
        section_gap: float = 1.0,
    ):
        self.font_size = max(9.0, min(13.0, float(font_size)))
        self.line_height = max(1.2, min(2.0, float(line_height)))
        self.section_gap = max(0.5, min(2.0, float(section_gap)))

    @classmethod
    def from_dict(cls, d: Dict[str, Any] = None) -> "StyleOptions":
        d = d or {}
        return cls(
            font_size=d.get("font_size", 10.5),
            line_height=d.get("line_height", 1.6),
            section_gap=d.get("section_gap", 1.0),
        )


class BaseTemplate(ABC):
    """模板基类"""

    name: str = "base"
    display_name: str = "基础模板"
    description: str = ""

    @abstractmethod
    def render_pdf(self, tokens: list, options: StyleOptions) -> bytes:
        """tokens: parse_md 返回的 token 流;返回 PDF 字节"""

    @abstractmethod
    def render_docx(self, doc: Document, tokens: list, options: StyleOptions) -> None:
        """原地修改 doc 对象"""
