"""班级管理 Pydantic Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ClassCreate(BaseModel):
    """创建班级"""
    class_no: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    major_id: int = Field(..., gt=0)
    advisor_id: Optional[int] = Field(None)
    grade: int = Field(..., gt=2000)


class ClassUpdate(BaseModel):
    """更新班级"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    advisor_id: Optional[int] = None


class ClassResponse(BaseModel):
    """班级响应"""
    id: int
    class_no: str
    name: str
    major_id: int
    advisor_id: Optional[int] = None
    grade: int
    created_at: datetime

    class Config:
        from_attributes = True


class ClassPageQuery(BaseModel):
    """班级分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=10000)
    college_id: Optional[int] = None
    major_id: Optional[int] = None
    grade: Optional[int] = None
    keyword: Optional[str] = None
