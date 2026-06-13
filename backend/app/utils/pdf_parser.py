"""PDF 解析 - V1 支持文本型 PDF(扫描件暂不支持 OCR)

pypdf 是纯 Python,无需系统库。
"""
import time
from io import BytesIO
from loguru import logger


def parse_pdf(content: bytes) -> dict:
    """解析 PDF 字节,返回 {text, paragraphs, sections, char_count}

    与 parse_docx 保持一致的数据结构,便于 file_service 统一处理。
    """
    t0 = time.time()
    try:
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(content))
    except Exception as e:
        logger.exception("PDF 解析失败(bytes 不可读)")
        raise ValueError(f"PDF 文件无法解析: {e}")

    paragraphs = []
    pages_ok = 0
    pages_fail = 0
    for idx, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
            pages_ok += 1
        except Exception as e:
            logger.warning(f"PDF 单页提取失败 page={idx+1} err={e}")
            text = ""
            pages_fail += 1
        # 按行拆,空行合并
        for line in text.split("\n"):
            line = line.strip()
            if line:
                paragraphs.append(line)

    full_text = "\n".join(paragraphs)
    if not full_text.strip():
        logger.warning(f"PDF 解析后无文本 pages={len(reader.pages)} ok={pages_ok} fail={pages_fail} (可能是扫描件或加密)")
        raise ValueError("PDF 未提取到文本,可能是扫描件或加密文件(暂不支持)")

    duration_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"PDF 解析成功 pages={len(reader.pages)} ok={pages_ok} fail={pages_fail} "
        f"chars={len(full_text)} lines={len(paragraphs)} duration={duration_ms}ms"
    )
    return {
        "text": full_text,
        "paragraphs": paragraphs,
        "sections": [],
        "char_count": len(full_text),
        "page_count": len(reader.pages),
    }
