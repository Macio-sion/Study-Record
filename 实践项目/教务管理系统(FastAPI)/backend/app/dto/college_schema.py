"""
学院管理 Pydantic Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CollegeCreate(BaseModel):
    """创建学院"""
    code: str = Field(..., min_length=1, max_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CollegeUpdate(BaseModel):
    """更新学院"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CollegeResponse(BaseModel):
    """学院响应"""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CollegePageQuery(BaseModel):
    """学院分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=10000)
    keyword: Optional[str] = None


# ========== 学院概览 ==========

class CollegeOverviewMajor(BaseModel):
    """概览-专业信息"""
    id: int
    name: str
    student_count: int = 0


class CollegeOverviewClass(BaseModel):
    """概览-班级信息"""
    id: int
    name: str
    student_count: int = 0


class CollegeOverviewCourse(BaseModel):
    """概览-课程统计"""
    major_name: str
    course_count: int = 0


class CollegeOverviewResponse(BaseModel):
    """学院概览响应"""
    college_name: str
    major_count: int = 0
    class_count: int = 0
    student_count: int = 0
    teacher_count: int = 0
    course_count: int = 0
    majors: list[CollegeOverviewMajor] = []
    classes: list[CollegeOverviewClass] = []
    courses: list[CollegeOverviewCourse] = []
