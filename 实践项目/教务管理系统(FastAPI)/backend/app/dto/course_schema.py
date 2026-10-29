"""课程管理 Pydantic Schema"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    """创建课程"""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    semester_id: int = Field(..., gt=0)
    college_id: int = Field(..., gt=0)
    teacher_id: int = Field(..., gt=0)
    credit: Decimal = Field(..., ge=0, le=20)
    max_capacity: int = Field(..., gt=0)
    hours: int = Field(..., gt=0)
    type: str = Field(..., description="必修/选修")
    category: str = Field('', max_length=30, description='课程分类：通识教育/学科基础/专业核心/专业方向/实践教学')
    description: Optional[str] = None


class CourseUpdate(BaseModel):
    """更新课程"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    teacher_id: Optional[int] = Field(None, gt=0)
    credit: Optional[Decimal] = Field(None, ge=0, le=20)
    max_capacity: Optional[int] = Field(None, gt=0)
    hours: Optional[int] = Field(None, gt=0)
    type: Optional[str] = None
    category: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = None


class CourseResponse(BaseModel):
    """课程响应"""
    id: int
    code: str
    name: str
    semester_id: int
    college_id: int
    teacher_id: int
    credit: Decimal
    max_capacity: int
    selected_count: int
    hours: int
    type: str
    category: str = ''
    description: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CoursePageQuery(BaseModel):
    """课程分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=10000)
    semester_id: Optional[int] = None
    college_id: Optional[int] = None
    teacher_id: Optional[int] = None
    type: Optional[str] = None
    category: Optional[str] = None
    keyword: Optional[str] = None
