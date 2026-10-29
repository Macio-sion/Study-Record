"""
教师管理 Pydantic Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TeacherCreate(BaseModel):
    """创建教师"""
    teacher_no: str = Field(..., min_length=1, max_length=20)
    user_id: int = Field(..., gt=0)
    college_id: int = Field(..., gt=0)
    gender: str = Field(..., min_length=1, max_length=4)
    title: Optional[str] = Field(None, max_length=50)


class TeacherUpdate(BaseModel):
    """更新教师"""
    college_id: Optional[int] = Field(None, gt=0)
    gender: Optional[str] = Field(None, min_length=1, max_length=4)
    title: Optional[str] = Field(None, max_length=50)


class TeacherResponse(BaseModel):
    """教师响应"""
    id: int
    teacher_no: str
    user_id: int
    college_id: int
    gender: str
    title: Optional[str] = None
    name: str = ''
    phone: Optional[str] = None
    email: Optional[str] = None
    college_name: str = ''
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeacherPageQuery(BaseModel):
    """教师分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=10000)
    college_id: Optional[int] = None
    keyword: Optional[str] = None
