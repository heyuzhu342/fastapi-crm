"""
通用 Schema：统一响应、分页
"""
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


# ── 统一响应格式 ─────────────────────────────────
class ResponseModel(BaseModel, Generic[T]):
    """统一 API 响应"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="提示信息")
    data: Optional[T] = Field(default=None, description="响应数据")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": {}
            }
        }


class ResponseList(BaseModel, Generic[T]):
    """带分页的列表响应"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="提示信息")
    data: list[T] = Field(default_factory=list, description="数据列表")
    meta: dict = Field(
        default_factory=lambda: {
            "page": 1,
            "page_size": 20,
            "total": 0,
            "total_pages": 0,
        },
        description="分页元数据"
    )


# ── 分页请求 ─────────────────────────────────────
class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    sort_by: Optional[str] = Field(default="created_at", description="排序字段")
    order: str = Field(default="desc", description="排序方向: asc/desc")
    search: Optional[str] = Field(default=None, description="搜索关键词")
