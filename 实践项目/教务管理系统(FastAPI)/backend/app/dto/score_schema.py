"""成绩管理 Pydantic Schema"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class ScoreCreate(BaseModel):
    """录入成绩"""
    student_id: int = Field(..., gt=0)
    course_id: int = Field(..., gt=0)
    semester_id: int = Field(..., gt=0)
    teacher_id: int = Field(..., gt=0)
    score: Decimal = Field(..., ge=0, le=100)


class ScoreUpdate(BaseModel):
    """修改成绩"""
    score: Decimal = Field(..., ge=0, le=100)


class ScoreResponse(BaseModel):
    """成绩响应"""
    id: int
    student_id: int
    course_id: int
    semester_id: int
    teacher_id: int
    score: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScorePageQuery(BaseModel):
    """成绩分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    student_id: Optional[int] = None
    course_id: Optional[int] = None
    semester_id: Optional[int] = None
    college_id: Optional[int] = None
    major_id: Optional[int] = None
    keyword: Optional[str] = None
