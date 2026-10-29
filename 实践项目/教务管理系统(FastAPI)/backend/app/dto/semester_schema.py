"""学期管理 Pydantic Schema"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class SemesterCreate(BaseModel):
    """创建学期"""
    name: str = Field(..., min_length=1, max_length=20)
    start_date: date
    end_date: date
    is_current: bool = False


class SemesterUpdate(BaseModel):
    """更新学期"""
    name: Optional[str] = Field(None, min_length=1, max_length=20)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None


class SemesterResponse(BaseModel):
    """学期响应"""
    id: int
    name: str
    start_date: date
    end_date: date
    is_current: bool
    created_at: datetime

    class Config:
        from_attributes = True
