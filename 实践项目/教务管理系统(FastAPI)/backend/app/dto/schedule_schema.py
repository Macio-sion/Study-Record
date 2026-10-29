"""排课管理 Pydantic Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    """创建排课"""
    course_id: int = Field(..., gt=0)
    classroom_id: int = Field(..., gt=0)
    teacher_id: int = Field(..., gt=0)
    semester_id: int = Field(..., gt=0)
    week_start: int = Field(..., ge=1, le=20)
    week_end: int = Field(..., ge=1, le=20)
    day_of_week: int = Field(..., ge=1, le=7)
    period_start: int = Field(..., ge=1, le=12)
    period_end: int = Field(..., ge=1, le=12)


class ScheduleUpdate(BaseModel):
    """更新排课"""
    classroom_id: Optional[int] = Field(None, gt=0)
    week_start: Optional[int] = Field(None, ge=1, le=20)
    week_end: Optional[int] = Field(None, ge=1, le=20)
    day_of_week: Optional[int] = Field(None, ge=1, le=7)
    period_start: Optional[int] = Field(None, ge=1, le=12)
    period_end: Optional[int] = Field(None, ge=1, le=12)


class ScheduleResponse(BaseModel):
    """排课响应"""
    id: int
    course_id: int
    classroom_id: int
    teacher_id: int
    semester_id: int
    course_name: str = ''
    teacher_name: str = ''
    classroom_name: str = ''
    semester_name: str = ''
    week_range: str = ''
    week_start: int
    week_end: int
    day_of_week: int
    period_start: int
    period_end: int
    created_at: datetime

    class Config:
        from_attributes = True


class SchedulePageQuery(BaseModel):
    """排课分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    semester_id: Optional[int] = None
    teacher_id: Optional[int] = None
    classroom_id: Optional[int] = None
