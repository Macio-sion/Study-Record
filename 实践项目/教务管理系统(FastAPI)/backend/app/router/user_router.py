"""
用户管理路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.common.response import success, success_page
from app.common.permission import get_current_user, require_role
from app.model.user import User
from app.dto.user_schema import (
    UserCreate, UserUpdate, UserPageQuery, ChangePasswordRequest, UserResponse
)
from app.service import user_service

user_router = APIRouter(prefix="/api/users", tags=["用户管理"])


@user_router.get("/me", summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取当前登录用户的详细信息（含关联档案）"""
    data = UserResponse.model_validate(current_user).model_dump()
    # 查询关联的学生/教师档案
    if current_user.role_code == 'student':
        from app.model.student import Student
        result = await db.execute(
            select(Student).where(Student.user_id == current_user.id)
        )
        student = result.scalar_one_or_none()
        if student:
            data['student'] = {'id': student.id, 'student_no': student.student_no, 'gender': student.gender, 'enrollment_year': student.enrollment_year}
    elif current_user.role_code == 'teacher':
        from app.model.teacher import Teacher
        result = await db.execute(
            select(Teacher).where(Teacher.user_id == current_user.id)
        )
        teacher = result.scalar_one_or_none()
        if teacher:
            data['teacher'] = {'id': teacher.id, 'teacher_no': teacher.teacher_no, 'gender': teacher.gender, 'title': teacher.title}
    return success(data=data)


@user_router.get("", summary="用户列表", dependencies=[Depends(require_role("admin"))])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    keyword: str = None,
    role_code: str = None,
    is_active: bool = None,
    db: AsyncSession = Depends(get_db),
):
    """分页获取用户列表（仅管理员）"""
    query = UserPageQuery(
        page=page,
        page_size=page_size,
        keyword=keyword,
        role_code=role_code,
        is_active=is_active,
    )
    items, total = await user_service.list_users(db, query)
    return success_page(items=items, total=total, page=page, page_size=page_size)


@user_router.get("/{user_id}", summary="获取用户详情")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """根据ID获取用户详情"""
    user = await user_service.get_user(db, user_id)
    return success(data=user)


@user_router.post("", summary="创建用户")
async def create_user(
    req: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """创建新用户（仅管理员）"""
    user = await user_service.create_user(db, req)
    return success(data=user)


@user_router.put("/password", summary="修改自己的密码")
async def change_my_password(
    req: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前登录用户修改自己的密码"""
    await user_service.change_password(db, current_user.id, req)
    return success(message="密码修改成功")


@user_router.put("/profile", summary="更新个人信息")
async def update_profile(
    real_name: str = None,
    phone: str = None,
    email: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前登录用户更新个人信息"""
    from app.model.user import User as UserModel
    stmt = select(UserModel).where(UserModel.id == current_user.id)
    result = await db.execute(stmt)
    user = result.scalar_one()
    if real_name is not None:
        user.real_name = real_name
    if phone is not None:
        user.phone = phone
    if email is not None:
        user.email = email
    await db.flush()
    return success(data=UserResponse.model_validate(user), message="个人信息已更新")


@user_router.put("/{user_id}", summary="更新用户")
async def update_user(
    user_id: int,
    req: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """更新用户信息（仅管理员）"""
    user = await user_service.update_user(db, user_id, req)
    return success(data=user)


@user_router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """删除用户（仅管理员）"""
    await user_service.delete_user(db, user_id)
    return success(message="删除成功")
