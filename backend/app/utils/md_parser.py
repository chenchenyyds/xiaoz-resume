"""MD 解析器 - 把 MD 文本解析成结构化 token 流,供 docx/pdf 共用

支持:
- # / ## / ### 标题
- - / * / • 列表(支持嵌套 - 展开为同级的缩进 bullet)
- **加粗** / *斜体* / `行内代码`
- > 引用
- 普通段落

输出: list[dict]
- {type: 'h1'/'h2'/'h3', content: str}                 # 标题用纯文本(简历场景标题不带格式)
- {type: 'p', runs: [{text, fmt}]}                     # 段落用 runs
- {type: 'ul'/'ol', items: [{runs: [{text, fmt, level}]}]}  # 列表用 runs,level 表示嵌套层级
- {type: 'blockquote', content: str}                   # 引用用纯文本

fmt 字段: 'b' / 'i' / 'code' / 'b/i' 组合(用 / 分隔)
"""
import time
import markdown as md_lib
from bs4 import BeautifulSoup, NavigableString
from loguru import logger


def parse_md(md_text: str) -> list:
    """MD -> token 流

    流程: markdown -> HTML -> BeautifulSoup 解析 -> tokens
    """
    if not md_text:
        return []

    t0 = time.time()
    html = md_lib.markdown(
        md_text, extensions=['extra', 'sane_lists', 'tables', 'fenced_code']
    )
    soup = BeautifulSoup(html, "html.parser")  # 纯 Python,避免 lxml/html5lib native 扩展

    tokens = []
    h1 = h2 = h3 = p_cnt = ul_cnt = ol_cnt = quote_cnt = 0

    for el in soup.children:
        if not hasattr(el, 'name') or el.name is None:
            continue
        name = (el.name or '').lower()
        if name == 'h1':
            tokens.append({'type': 'h1', 'content': el.get_text().strip()})
            h1 += 1
        elif name == 'h2':
            tokens.append({'type': 'h2', 'content': el.get_text().strip()})
            h2 += 1
        elif name == 'h3':
            tokens.append({'type': 'h3', 'content': el.get_text().strip()})
            h3 += 1
        elif name == 'h4':
            tokens.append({'type': 'h3', 'content': el.get_text().strip()})
            h3 += 1
        elif name == 'p':
            tokens.append({'type': 'p', 'runs': _collect_runs(el)})
            p_cnt += 1
        elif name == 'ul':
            tokens.append({'type': 'ul', 'items': _items_from_list(el, level=0)})
            ul_cnt += 1
        elif name == 'ol':
            tokens.append({'type': 'ol', 'items': _items_from_list(el, level=0)})
            ol_cnt += 1
        elif name == 'blockquote':
            tokens.append({'type': 'blockquote', 'content': el.get_text().strip()})
            quote_cnt += 1
        elif name == 'table':
            tokens.append({'type': 'p', 'runs': _collect_runs(el)})
            p_cnt += 1
        elif name == 'pre':
            tokens.append({'type': 'p', 'runs': [{'text': el.get_text(), 'fmt': 'code'}]})
            p_cnt += 1

    ms = int((time.time() - t0) * 1000)
    logger.debug(
        f"[md_parser] parsed h1={h1} h2={h2} h3={h3} p={p_cnt} "
        f"ul={ul_cnt} ol={ol_cnt} quote={quote_cnt} duration={ms}ms"
    )
    return tokens


def _items_from_list(ul_el, level: int = 0) -> list:
    """解析 <ul>/<ol> 元素,返回 [{runs: [{text, fmt, level}]}]

    嵌套的 ul/ol 会展开为同级 item(level+1)
    """
    items = []
    for li in ul_el.find_all('li', recursive=False):
        # 先看 li 的顶层内容(text + inline tags),跳过嵌套的 ul/ol
        runs = _collect_runs(li, skip_ul=True, level=level)
        if runs:
            items.append({'runs': runs})
        # 处理嵌套列表
        for nested in li.find_all(['ul', 'ol'], recursive=False):
            nested_type = nested.name.lower()
            items.extend(_items_from_list(nested, level=level + 1))
    return items


def _collect_runs(el, skip_ul: bool = False, level: int = 0) -> list:
    """递归收集一个元素内的所有文本片段和它们的格式

    返回 [{text, fmt, level}]
    fmt: 'b' / 'i' / 'code' / 组合用 / 分隔,如 'b/i'
    level: 嵌套层级(给 list 用,给 p 用永远 0)
    """
    runs = []

    def walk(node, fmt_stack, in_skip: bool = False):
        for child in node.children:
            if isinstance(child, NavigableString):
                text = str(child)
                if text:
                    runs.append({
                        'text': text,
                        'fmt': '/'.join(fmt_stack) if fmt_stack else '',
                        'level': level,
                    })
                continue
            name = (getattr(child, 'name', '') or '').lower()
            if not name:
                continue
            if name in ('ul', 'ol'):
                # 跳过嵌套列表(_items_from_list 会单独处理)
                continue
            if name in ('strong', 'b'):
                walk(child, fmt_stack + ['b'])
            elif name in ('em', 'i'):
                walk(child, fmt_stack + ['i'])
            elif name == 'code':
                walk(child, fmt_stack + ['code'])
            elif name == 'a':
                href = child.get('href', '') or ''
                text = child.get_text()
                if text:
                    runs.append({
                        'text': text,
                        'fmt': '/'.join(fmt_stack + ['link']) if fmt_stack else 'link',
                        'level': level,
                        'href': href,
                    })
            elif name == 'br':
                runs.append({
                    'text': '\n',
                    'fmt': '/'.join(fmt_stack) if fmt_stack else '',
                    'level': level,
                })
            else:
                walk(child, fmt_stack)

    walk(el, [])
    # 合并相邻同 fmt 的 runs
    return _merge_runs(runs)


def _merge_runs(runs: list) -> list:
    """合并相邻同 fmt 的 runs,减少碎片"""
    if not runs:
        return runs
    merged = [runs[0]]
    for r in runs[1:]:
        prev = merged[-1]
        if prev['fmt'] == r['fmt'] and prev.get('level', 0) == r.get('level', 0):
            prev['text'] += r['text']
        else:
            merged.append(r)
    return merged


def render_runs_to_html(runs: list) -> str:
    """把 runs 转成 reportlab Paragraph 可识别的 inline HTML 字符串

    - b -> <b>...</b>
    - i -> <i>...</i>
    - code -> <font face="Courier">...</font>
    - link -> <link href="...">...</link>(reportlab 用 <link>)
    """
    parts = []
    for r in runs:
        text = _escape(r['text'])
        fmt = r.get('fmt', '')
        if 'link' in fmt:
            href = _escape(r.get('href', ''))
            parts.append(f'<link href="{href}">{text}</link>')
        else:
            # 包外层 fmt
            wrapped = text
            if 'b' in fmt:
                wrapped = f'<b>{wrapped}</b>'
            if 'i' in fmt:
                wrapped = f'<i>{wrapped}</i>'
            if 'code' in fmt:
                # reportlab 不支持 <code>,转 <font face="Courier">
                wrapped = f'<font face="Courier">{wrapped}</font>'
            parts.append(wrapped)
    return "".join(parts)


def _escape(text: str) -> str:
    """转义 reportlab Paragraph 的特殊字符"""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )
