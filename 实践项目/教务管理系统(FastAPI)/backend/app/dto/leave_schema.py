"""请假审批 Pydantic Schema"""
from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class LeaveCreate(BaseModel):
    """学生提交请假申请"""
    course_id: int = Field(..., gt=0)
    leave_type: str
    leave_date: date
    reason: Optional[str] = Field(None, max_length=500)


class LeaveUpdate(BaseModel):
    """教师/学工处审批"""
    opinion: Optional[str] = Field(None, max_length=200)
    approved: bool  # True=通过, False=拒绝


class LeaveResponse(BaseModel):
    """请假响应"""
    id: int
    student_id: int
    student_name: Optional[str] = None
    course_id: int
    course_name: Optional[str] = None
    leave_type: str
    leave_date: date
    reason: Optional[str] = None
    status: str
    teacher_id: Optional[int] = None
    teacher_opinion: Optional[str] = None
    teacher_at: Optional[datetime] = None
    staff_id: Optional[int] = None
    staff_opinion: Optional[str] = None
    staff_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LeavePageQuery(BaseModel):
    """请假分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    student_id: Optional[int] = None
    course_id: Optional[int] = None
    status: Optional[str] = None
    teacher_id: Optional[int] = None
    keyword: Optional[str] = None
