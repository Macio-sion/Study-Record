"""作业管理 Pydantic Schema"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class AssignmentCreate(BaseModel):
    """发布作业"""
    course_id: int = Field(..., gt=0)
    teacher_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    content: Optional[str] = None
    deadline: datetime


class AssignmentUpdate(BaseModel):
    """更新作业"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    deadline: Optional[datetime] = None


class AssignmentResponse(BaseModel):
    """作业响应"""
    id: int
    course_id: int
    teacher_id: int
    title: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    deadline: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentPageQuery(BaseModel):
    """作业分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    course_id: Optional[int] = None
    keyword: Optional[str] = None


class SubmissionCreate(BaseModel):
    """提交作业"""
    assignment_id: int = Field(..., gt=0)
    student_id: int = Field(..., gt=0)
    content: Optional[str] = None


class SubmissionReview(BaseModel):
    """批阅作业"""
    score: Optional[Decimal] = Field(None, ge=0, le=100)
    comment: Optional[str] = Field(None, max_length=500)


class SubmissionResponse(BaseModel):
    """作业提交响应"""
    id: int
    assignment_id: int
    student_id: int
    content: Optional[str] = None
    file_path: Optional[str] = None
    score: Optional[Decimal] = None
    comment: Optional[str] = None
    status: str = 'submitted'
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
