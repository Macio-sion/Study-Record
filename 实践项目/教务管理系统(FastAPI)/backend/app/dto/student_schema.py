"""学生管理 Pydantic Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    """创建学生"""
    student_no: str = Field(..., min_length=1, max_length=20)
    user_id: int = Field(..., gt=0)
    major_id: int = Field(..., gt=0)
    class_id: int = Field(..., gt=0)
    gender: str = Field(..., min_length=1, max_length=4)
    enrollment_year: int = Field(..., gt=2000)


class StudentUpdate(BaseModel):
    """更新学生"""
    major_id: Optional[int] = Field(None, gt=0)
    class_id: Optional[int] = Field(None, gt=0)
    gender: Optional[str] = Field(None, min_length=1, max_length=4)


class StudentResponse(BaseModel):
    """学生响应"""
    id: int
    student_no: str
    user_id: int
    major_id: int
    class_id: int
    gender: str
    enrollment_year: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudentPageQuery(BaseModel):
    """学生分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=10000)
    college_id: Optional[int] = None
    major_id: Optional[int] = None
    class_id: Optional[int] = None
    enrollment_year: Optional[int] = None
    keyword: Optional[str] = None
