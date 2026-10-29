"""教室管理 Pydantic Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ClassroomCreate(BaseModel):
    """创建教室"""
    room_no: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    building: str = Field(..., min_length=1, max_length=50)
    capacity: int = Field(..., gt=0)
    type: str = Field(..., min_length=1, max_length=20)
    status: str = Field("available", min_length=1, max_length=10)


class ClassroomUpdate(BaseModel):
    """更新教室"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    building: Optional[str] = Field(None, min_length=1, max_length=50)
    capacity: Optional[int] = Field(None, gt=0)
    type: Optional[str] = Field(None, min_length=1, max_length=20)
    status: Optional[str] = Field(None, min_length=1, max_length=10)


class ClassroomResponse(BaseModel):
    """教室响应"""
    id: int
    room_no: str
    name: str
    building: str
    capacity: int
    type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ClassroomPageQuery(BaseModel):
    """教室分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=10000)
    building: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    keyword: Optional[str] = None
