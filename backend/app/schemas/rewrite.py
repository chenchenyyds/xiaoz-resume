"""改写相关 schema"""

from pydantic import BaseModel, Field
from typing import Optional, List


class PartialRewriteReq(BaseModel):
    text: str = Field(..., min_length=10, max_length=3000)
    title: Optional[str] = Field(
        default=None, max_length=50, description="这段的标题,如'项目经历'"
    )
    style_hint: Optional[str] = Field(
        default=None, max_length=100, description="风格提示,如'更口语化'"
    )


class PartialRewriteResp(BaseModel):
    output_text: str
    explanation: str  # 这次改了什么、为什么
    points_cost: int
    points_remaining: int


class FullRewriteReq(BaseModel):
    file_id: int = Field(..., description="已上传的简历文件 ID")
    jd_text: Optional[str] = Field(
        default=None, max_length=8000, description="JD 文本,V1 用户手动粘贴"
    )
    style_hint: Optional[str] = Field(default=None, max_length=100)


class FullRewriteResp(BaseModel):
    file_id: int  # 生成的简历文件 ID
    output_text: str
    improvement_points: List[str]  # 5 条优化点
    points_cost: int
    points_remaining: int
