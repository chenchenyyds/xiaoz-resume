"""改写相关 schema"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class PartialRewriteReq(BaseModel):
    text: str = Field(..., min_length=10, max_length=3000)
    title: Optional[str] = Field(
        default=None, max_length=50, description="这段的标题,如'项目经历'"
    )
    style_hint: Optional[str] = Field(
        default=None, max_length=100, description="风格提示,如'更口语化'"
    )
    template_code: Optional[str] = Field(
        default="classic", max_length=50, description="模板代码(classic/modern/sidebar)"
    )
    style_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="样式参数 {font_size, line_height, section_gap}",
    )


class PartialRewriteResp(BaseModel):
    output_text: str
    explanation: str
    points_cost: int
    points_remaining: int


class FullRewriteReq(BaseModel):
    file_id: int = Field(..., description="已上传的简历文件 ID")
    jd_text: Optional[str] = Field(
        default=None, max_length=8000, description="JD 文本,V1 用户手动粘贴"
    )
    style_hint: Optional[str] = Field(default=None, max_length=100)
    template_code: Optional[str] = Field(
        default="classic", max_length=50, description="模板代码(classic/modern/sidebar)"
    )
    style_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="样式参数 {font_size, line_height, section_gap}",
    )


class FullRewriteResp(BaseModel):
    file_id: int
    output_text: str
    improvement_points: List[str]
    points_cost: int
    points_remaining: int


class TemplateInfo(BaseModel):
    code: str
    display_name: str
    description: str


class TemplateListResp(BaseModel):
    templates: List[TemplateInfo]
