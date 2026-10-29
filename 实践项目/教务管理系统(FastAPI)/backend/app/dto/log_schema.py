"""操作日志 Pydantic Schema"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LogResponse(BaseModel):
    """日志响应"""
    id: int
    user_id: int
    action: str
    module: str
    target_id: Optional[int] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LogPageQuery(BaseModel):
    """日志分页查询"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    user_id: Optional[int] = None
    module: Optional[str] = None
    action: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    keyword: Optional[str] = None
