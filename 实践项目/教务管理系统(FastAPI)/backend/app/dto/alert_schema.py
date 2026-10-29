"""学业预警 Pydantic Schema"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    """创建预警记录"""
    student_id: int = Field(..., gt=0)
    semester_id: int = Field(..., gt=0)
    alert_level: str = Field(..., max_length=20)
    alert_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    attendance_rate: Optional[Decimal] = None
    failed_count: Optional[int] = Field(None, ge=0)


class AlertHandle(BaseModel):
    """处理预警"""
    handle_result: Optional[str] = Field(None, max_length=500)


class AlertResponse(BaseModel):
    """预警响应"""
    id: int
    student_id: int
    semester_id: int
    alert_level: str
    alert_type: Optional[str] = None
    description: Optional[str] = None
    attendance_rate: Optional[Decimal] = None
    failed_count: Optional[int] = None
    status: str
    handler_id: Optional[int] = None
    handle_result: Optional[str] = None
    handled_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertPageQuery(BaseModel):
    """预警分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    student_id: Optional[int] = None
    semester_id: Optional[int] = None
    alert_level: Optional[str] = None
    status: Optional[str] = None
    keyword: Optional[str] = None
