"""通知公告 Pydantic Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class NoticeCreate(BaseModel):
    """创建通知"""
    title: str = Field(..., min_length=1, max_length=200)
    content: Optional[str] = None
    target_role: str = Field('all', pattern=r'^(all|teacher|student)$')
    college_id: Optional[int] = None
    major_id: Optional[int] = None


class NoticeUpdate(BaseModel):
    """更新通知"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    target_role: Optional[str] = Field(None, pattern=r'^(all|teacher|student)$')
    college_id: Optional[int] = None
    major_id: Optional[int] = None
    is_published: Optional[bool] = None


class NoticeResponse(BaseModel):
    """通知响应"""
    id: int
    title: str
    content: Optional[str] = None
    publisher_id: int
    publisher_name: Optional[str] = None
    target_role: str
    college_id: Optional[int] = None
    college_name: Optional[str] = None
    major_id: Optional[int] = None
    major_name: Optional[str] = None
    is_published: bool
    published_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NoticePageQuery(BaseModel):
    """通知分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    is_published: Optional[bool] = None
    target_role: Optional[str] = None
    college_id: Optional[int] = None
    major_id: Optional[int] = None
    keyword: Optional[str] = None


class NoticeRecallCreate(BaseModel):
    """撤回申请"""
    reason: Optional[str] = None


class NoticeRecallReview(BaseModel):
    """审批撤回申请"""
    approved: bool = True
    comment: Optional[str] = None
