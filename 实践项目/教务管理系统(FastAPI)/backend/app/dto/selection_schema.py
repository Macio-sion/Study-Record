"""选课管理 Pydantic Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CourseSelectionCreate(BaseModel):
    """选课请求"""
    course_id: int = Field(..., gt=0)
    student_id: int = Field(0)   # 后端自动填充
    semester_id: int = Field(0)  # 后端自动填充


class SelectionResponse(BaseModel):
    """选课记录响应"""
    id: int
    student_id: int
    course_id: int
    semester_id: int
    selected_at: datetime
    status: str
    # 关联字段（列表查询时填充）
    student_name: Optional[str] = None
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    course_type: Optional[str] = None
    course_credit: Optional[float] = None
    teacher_name: Optional[str] = None
    semester_name: Optional[str] = None

    class Config:
        from_attributes = True


class SelectionPageQuery(BaseModel):
    """选课分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    student_id: Optional[int] = None
    course_id: Optional[int] = None
    semester_id: Optional[int] = None
    college_id: Optional[int] = None
    major_id: Optional[int] = None
    status: Optional[str] = None
