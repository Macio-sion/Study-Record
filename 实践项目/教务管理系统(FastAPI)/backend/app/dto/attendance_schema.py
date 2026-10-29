"""考勤管理 Pydantic Schema"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class AttendanceCreate(BaseModel):
    """创建点名记录"""
    course_id: int = Field(..., gt=0)
    student_id: int = Field(..., gt=0)
    teacher_id: int = Field(..., gt=0)
    date: date
    status: str = Field(..., description="present/absent/late/leave")
    remark: Optional[str] = Field(None, max_length=200)


class AttendanceUpdate(BaseModel):
    """更新考勤"""
    status: Optional[str] = None
    remark: Optional[str] = Field(None, max_length=200)


class AttendanceResponse(BaseModel):
    """考勤记录响应"""
    id: int
    course_id: int
    student_id: int
    teacher_id: int
    date: date
    status: str
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttendancePageQuery(BaseModel):
    """考勤分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    course_id: Optional[int] = None
    student_id: Optional[int] = None
    date: Optional[date] = None
    status: Optional[str] = None


class AttendanceStatsResponse(BaseModel):
    """考勤统计响应"""
    total: int = 0
    present: int = 0
    absent: int = 0
    late: int = 0
    leave: int = 0
    rate: float = 0.0  # 出勤率
