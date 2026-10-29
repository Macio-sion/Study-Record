"""
专业管理 Pydantic Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MajorCreate(BaseModel):
    """创建专业"""
    code: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    college_id: int = Field(..., gt=0)
    duration: int = Field(4, ge=2, le=8)
    degree: str = Field(..., min_length=1, max_length=20)


class MajorUpdate(BaseModel):
    """更新专业"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    duration: Optional[int] = Field(None, ge=2, le=8)
    degree: Optional[str] = Field(None, min_length=1, max_length=20)


class MajorResponse(BaseModel):
    """专业响应"""
    id: int
    code: str
    name: str
    college_id: int
    duration: int
    degree: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MajorPageQuery(BaseModel):
    """专业分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=10000)
    college_id: Optional[int] = None
    keyword: Optional[str] = None
