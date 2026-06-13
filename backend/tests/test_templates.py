"""模板系统测试 - 决策 21

覆盖:
- 3 个模板都能生成 PDF
- 3 个模板生成的 PDF 不一样(差异性)
- 默认模板 = classic
- 未知 template_code 降级 classic
- style_options 范围校验
- registry.list_templates() 返回 3 个
"""

import pytest
from app.utils.pdf_builder import build_pdf
from app.utils.docx_parser import build_docx
from app.utils.templates.registry import get_template, list_templates
from app.utils.templates.base import StyleOptions


SAMPLE_MD = """# 张三

13800000000 | zhangsan@example.com

## 专业总结

5年后端开发工程师。

## 专业技能

- Java：精通
- AI：掌握
- 全栈：熟练

## 工作经历

中科软 | 2021-2026

- 主导 5 个项目
- 性能优化 75%
"""


def test_list_templates_returns_three():
    """内置 3 个模板"""
    tmpls = list_templates()
    codes = [t["code"] for t in tmpls]
    assert set(codes) == {"classic", "modern", "sidebar"}


def test_unknown_template_falls_back_to_classic():
    """未知 code 降级 classic"""
    tmpl = get_template("not_exist")
    assert tmpl.name == "classic"


def test_three_templates_generate_distinct_pdfs():
    """3 模板生成的 PDF 大小不同(差异性)"""
    pdfs = {}
    for code in ["classic", "modern", "sidebar"]:
        pdfs[code] = build_pdf(SAMPLE_MD, template_code=code)
    # 大小不全相等(至少 sidebar 因有 Frame 背景画得不一样)
    assert pdfs["classic"] != pdfs["sidebar"]
    assert pdfs["modern"] != pdfs["sidebar"]


def test_three_templates_generate_distinct_docx():
    """3 模板生成的 docx 大小/颜色配置不同"""
    docxs = {}
    for code in ["classic", "modern", "sidebar"]:
        docxs[code] = build_docx(SAMPLE_MD, template_code=code)
    # 颜色不同 → XML bytes 不同
    assert docxs["classic"] != docxs["modern"]


def test_style_options_clamp():
    """style_options 范围校验"""
    # font_size 越界会被 clamp
    opts = StyleOptions.from_dict(
        {"font_size": 99, "line_height": 0.1, "section_gap": 99}
    )
    assert opts.font_size == 13.0  # clamp 到 max
    assert opts.line_height == 1.2  # clamp 到 min
    assert opts.section_gap == 2.0  # clamp 到 max


def test_default_template_is_classic():
    """不传 template_code 走 classic"""
    pdf_default = build_pdf(SAMPLE_MD)
    pdf_classic = build_pdf(SAMPLE_MD, template_code="classic")
    # 字节等(都走 classic),但 PDF metadata 里 title 可能不同
    assert len(pdf_default) == len(pdf_classic)
    # 解码页数应该一致
    import io

    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    n1 = len(PdfReader(io.BytesIO(pdf_default)).pages)
    n2 = len(PdfReader(io.BytesIO(pdf_classic)).pages)
    assert n1 == n2 == 1


def test_pdf_validates_magic_bytes():
    """生成的 PDF 是真 PDF"""
    pdf = build_pdf(SAMPLE_MD, template_code="classic")
    assert pdf[:4] == b"%PDF"


def test_docx_validates_magic_bytes():
    """生成的 docx 是真 docx"""
    docx = build_docx(SAMPLE_MD, template_code="modern")
    assert docx[:4] == b"PK\x03\x04"  # zip magic
