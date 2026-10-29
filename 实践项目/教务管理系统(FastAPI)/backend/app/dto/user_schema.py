"""
用户模块 Pydantic Schema
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ========== 登录 ==========

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=100, description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    token: str = Field(..., description="JWT Token")
    username: str
    real_name: str
    role_code: str
    user_id: int
    managed_college_id: int | None = None


# ========== 用户 CRUD ==========

class UserCreate(BaseModel):
    """创建用户"""
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    real_name: str = Field(..., min_length=1, max_length=50)
    role_code: str = Field(..., description="角色编码: admin/academic_staff/teacher/student")
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    is_active: bool = Field(True)

    @field_validator('role_code')
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = {'admin', 'academic_staff', 'teacher', 'student'}
        if v not in valid_roles:
            raise ValueError(f'角色编码必须为: {", ".join(valid_roles)}')
        return v


class UserUpdate(BaseModel):
    """更新用户"""
    real_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    real_name: str
    role_code: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserPageQuery(BaseModel):
    """用户分页查询参数"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    keyword: Optional[str] = Field(None, description="搜索关键词（用户名/姓名）")
    role_code: Optional[str] = Field(None, description="按角色筛选")
    is_active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    """修改密码"""
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6, max_length=100)
