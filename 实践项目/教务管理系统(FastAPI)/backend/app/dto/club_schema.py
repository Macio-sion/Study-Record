"""社团管理 Pydantic Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ClubCreate(BaseModel):
    """创建社团"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    advisor_id: int = Field(..., gt=0)


class ClubUpdate(BaseModel):
    """更新社团信息"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    advisor_id: Optional[int] = Field(None, gt=0)


class ClubResponse(BaseModel):
    """社团响应"""
    id: int
    name: str
    description: Optional[str] = None
    advisor_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ClubPageQuery(BaseModel):
    """社团分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    name: Optional[str] = None


class MemberJoin(BaseModel):
    """加入社团"""
    club_id: int = Field(..., gt=0)


class MemberResponse(BaseModel):
    """社员响应"""
    id: int
    club_id: int
    student_id: int
    role: str
    status: str = 'approved'
    joined_at: datetime

    model_config = {"from_attributes": True}


class MemberApprove(BaseModel):
    """审批社团申请"""
    approved: bool  # True=通过, False=拒绝
    role: Optional[str] = Field("member", max_length=20)
