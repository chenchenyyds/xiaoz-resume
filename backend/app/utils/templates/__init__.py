"""模板系统 - 简历 PDF/DOCX 样式可插拔

设计要点:
- BaseTemplate 是抽象基类,定义 render_pdf / render_docx 接口
- 每个具体模板自带字体配置、颜色主题、布局、样式集合
- 模板通过 TemplateRegistry 单例管理,代码里硬编码 3 个内置模板
- style_options 覆盖默认参数(font_size / line_height / section_gap)
"""
