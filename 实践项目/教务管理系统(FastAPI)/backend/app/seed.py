"""
种子数据初始化脚本
创建默认角色、权限和管理员账户
运行方式: python -m app.seed
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.model.role import Role
from app.model.permission import Permission
from app.model.role_permission import RolePermission
from app.model.user import User
from app.common.security import hash_password


ROLES = [
    {"code": "admin", "name": "超级管理员", "description": "系统超级管理员，拥有所有权限"},
    {"code": "academic_staff", "name": "教务员", "description": "教务管理人员"},
    {"code": "teacher", "name": "教师", "description": "授课教师"},
    {"code": "student", "name": "学生", "description": "在校学生"},
]

PERMISSIONS = [
    # 用户管理
    {"code": "user:list", "name": "用户列表", "module": "用户管理"},
    {"code": "user:create", "name": "创建用户", "module": "用户管理"},
    {"code": "user:update", "name": "更新用户", "module": "用户管理"},
    {"code": "user:delete", "name": "删除用户", "module": "用户管理"},
    # 学院管理
    {"code": "college:list", "name": "学院列表", "module": "学院管理"},
    {"code": "college:manage", "name": "学院管理", "module": "学院管理"},
    # 教师管理
    {"code": "teacher:list", "name": "教师列表", "module": "教师管理"},
    {"code": "teacher:manage", "name": "教师管理", "module": "教师管理"},
    # 学生管理
    {"code": "student:list", "name": "学生列表", "module": "学生管理"},
    {"code": "student:manage", "name": "学生管理", "module": "学生管理"},
    # 课程管理
    {"code": "course:list", "name": "课程列表", "module": "课程管理"},
    {"code": "course:manage", "name": "课程管理", "module": "课程管理"},
]

# admin 角色拥有所有权限的角色编码列表
ADMIN_ROLE_PERMS = [p["code"] for p in PERMISSIONS]
# academic_staff 拥有大部分管理权限
STAFF_ROLE_PERMS = [
    "user:list", "teacher:list", "teacher:manage", "student:list", "student:manage",
    "course:list", "course:manage", "college:list",
]
# teacher 只有查看权限
TEACHER_ROLE_PERMS = ["user:list", "teacher:list", "student:list", "course:list", "college:list"]
# student 只有基本查看权限
STUDENT_ROLE_PERMS = ["user:list", "student:list", "course:list"]

ROLE_PERM_MAP = {
    "admin": ADMIN_ROLE_PERMS,
    "academic_staff": STAFF_ROLE_PERMS,
    "teacher": TEACHER_ROLE_PERMS,
    "student": STUDENT_ROLE_PERMS,
}

DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123",
    "real_name": "系统管理员",
    "role_code": "admin",
}


async def seed():
    async with AsyncSessionLocal() as db:
        # 1. 创建角色
        for r in ROLES:
            exists = await db.execute(select(Role).where(Role.code == r["code"]))
            if exists.scalar_one_or_none() is None:
                db.add(Role(**r))
        await db.flush()

        # 2. 创建权限
        for p in PERMISSIONS:
            exists = await db.execute(select(Permission).where(Permission.code == p["code"]))
            if exists.scalar_one_or_none() is None:
                db.add(Permission(**p))
        await db.flush()

        # 3. 创建角色-权限关联
        for role_code, perm_codes in ROLE_PERM_MAP.items():
            role = (await db.execute(select(Role).where(Role.code == role_code))).scalar_one()
            for pcode in perm_codes:
                perm = (await db.execute(select(Permission).where(Permission.code == pcode))).scalar_one()
                exists = await db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == perm.id,
                    )
                )
                if exists.scalar_one_or_none() is None:
                    db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        await db.flush()

        # 4. 创建默认管理员
        admin_exists = await db.execute(
            select(User).where(User.username == DEFAULT_ADMIN["username"])
        )
        if admin_exists.scalar_one_or_none() is None:
            admin = User(
                username=DEFAULT_ADMIN["username"],
                password_hash=hash_password(DEFAULT_ADMIN["password"]),
                real_name=DEFAULT_ADMIN["real_name"],
                role_code=DEFAULT_ADMIN["role_code"],
                is_active=True,
            )
            db.add(admin)

        await db.commit()
        print("种子数据初始化完成！")
        print(f"  角色: {len(ROLES)} 个")
        print(f"  权限: {len(PERMISSIONS)} 个")
        print(f"  默认管理员: admin / admin123")


if __name__ == "__main__":
    asyncio.run(seed())
