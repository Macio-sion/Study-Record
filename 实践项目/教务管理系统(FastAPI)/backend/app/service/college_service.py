"""
学院与专业管理 Service
"""
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.college_dao import college_dao, major_dao
from app.model.college import College
from app.model.major import Major
from app.model.student import Student
from app.model.class_model import Class
from app.model.user import User
from app.model.course import Course
from app.dto.college_schema import (
    CollegeCreate, CollegeUpdate, CollegeResponse, CollegePageQuery,
    CollegeOverviewResponse, CollegeOverviewMajor, CollegeOverviewClass, CollegeOverviewCourse,
)
from app.dto.major_schema import (
    MajorCreate, MajorUpdate, MajorResponse, MajorPageQuery,
)
from app.common.exception import ConflictException, NotFoundException


# ========== 学院管理 ==========

async def create_college(db: AsyncSession, req: CollegeCreate) -> CollegeResponse:
    college = College(code=req.code, name=req.name, description=req.description)
    college = await college_dao.create(db, college)
    return CollegeResponse.model_validate(college)


async def update_college(db: AsyncSession, college_id: int, req: CollegeUpdate) -> CollegeResponse:
    college = await college_dao.get_by_id(db, college_id)
    if not college:
        raise NotFoundException(f"学院不存在: id={college_id}")
    college = await college_dao.update(db, college, name=req.name, description=req.description)
    return CollegeResponse.model_validate(college)


async def delete_college(db: AsyncSession, college_id: int) -> bool:
    if not await college_dao.delete(db, college_id):
        raise NotFoundException(f"学院不存在: id={college_id}")
    return True


async def get_college(db: AsyncSession, college_id: int) -> CollegeResponse:
    college = await college_dao.get_by_id(db, college_id)
    if not college:
        raise NotFoundException(f"学院不存在: id={college_id}")
    return CollegeResponse.model_validate(college)


async def list_colleges(db: AsyncSession, query: CollegePageQuery) -> tuple[list[CollegeResponse], int]:
    filters = []
    if query.keyword:
        filters.append(
            or_(College.name.like(f"%{query.keyword}%"), College.code.like(f"%{query.keyword}%"))
        )
    items, total = await college_dao.get_all(
        db, page=query.page, page_size=query.page_size, filters=filters,
        order_by=College.code,
    )
    return [CollegeResponse.model_validate(c) for c in items], total


async def get_all_colleges(db: AsyncSession) -> list[CollegeResponse]:
    """获取所有学院（下拉选择用）"""
    items, _ = await college_dao.get_all(db, page=1, page_size=1000, order_by=College.code)
    return [CollegeResponse.model_validate(c) for c in items]


# ========== 专业管理 ==========

async def create_major(db: AsyncSession, req: MajorCreate) -> MajorResponse:
    # 检查学院是否存在
    college = await college_dao.get_by_id(db, req.college_id)
    if not college:
        raise NotFoundException(f"学院不存在: id={req.college_id}")

    major = Major(
        code=req.code, name=req.name, college_id=req.college_id,
        duration=req.duration, degree=req.degree,
    )
    major = await major_dao.create(db, major)
    return MajorResponse.model_validate(major)


async def update_major(db: AsyncSession, major_id: int, req: MajorUpdate) -> MajorResponse:
    major = await major_dao.get_by_id(db, major_id)
    if not major:
        raise NotFoundException(f"专业不存在: id={major_id}")
    major = await major_dao.update(db, major, name=req.name, duration=req.duration, degree=req.degree)
    return MajorResponse.model_validate(major)


async def delete_major(db: AsyncSession, major_id: int) -> bool:
    if not await major_dao.delete(db, major_id):
        raise NotFoundException(f"专业不存在: id={major_id}")
    return True


async def get_major(db: AsyncSession, major_id: int) -> MajorResponse:
    major = await major_dao.get_by_id(db, major_id)
    if not major:
        raise NotFoundException(f"专业不存在: id={major_id}")
    return MajorResponse.model_validate(major)


async def list_majors(db: AsyncSession, query: MajorPageQuery) -> tuple[list[MajorResponse], int]:
    filters = []
    if query.college_id:
        filters.append(Major.college_id == query.college_id)
    if query.keyword:
        filters.append(
            or_(Major.name.like(f"%{query.keyword}%"), Major.code.like(f"%{query.keyword}%"))
        )
    items, total = await major_dao.get_all(
        db, page=query.page, page_size=query.page_size, filters=filters,
        order_by=Major.code,
    )
    return [MajorResponse.model_validate(m) for m in items], total


# ========== 学院概览（聚合查询） ==========

async def get_college_overview(db: AsyncSession, college_id: int) -> CollegeOverviewResponse:
    """获取学院信息概览数据"""
    # 学院名称
    college = await college_dao.get_by_id(db, college_id)
    if not college:
        raise NotFoundException(f"学院不存在: id={college_id}")

    # 专业列表 + 各专业学生数
    result = await db.execute(
        select(Major.id, Major.name, func.count(Student.id).label('cnt'))
        .outerjoin(Student, Student.major_id == Major.id)
        .where(Major.college_id == college_id)
        .group_by(Major.id, Major.name)
    )
    major_rows = result.all()

    # 班级列表 + 各班级学生数
    result = await db.execute(
        select(Class.id, Class.name, func.count(Student.id).label('cnt'))
        .outerjoin(Student, Student.class_id == Class.id)
        .join(Major, Class.major_id == Major.id)
        .where(Major.college_id == college_id)
        .group_by(Class.id, Class.name)
    )
    class_rows = result.all()

    # 学生总数
    result = await db.execute(
        select(func.count(Student.id))
        .join(Major, Student.major_id == Major.id)
        .where(Major.college_id == college_id)
    )
    student_count = result.scalar() or 0

    # 教师总数（属于该学院的）
    result = await db.execute(
        select(func.count(User.id))
        .where(User.role_code == 'teacher', User.managed_college_id == college_id)
    )
    teacher_count = result.scalar() or 0

    # 课程统计（按专业分组）
    result = await db.execute(
        select(Major.name, func.count(Course.id).label('cnt'))
        .outerjoin(Course, Course.college_id == college_id)
        .where(Major.college_id == college_id)
        .group_by(Major.id, Major.name)
        .order_by(func.count(Course.id).desc())
    )
    course_rows = result.all()

    return CollegeOverviewResponse(
        college_name=college.name,
        major_count=len(major_rows),
        class_count=len(class_rows),
        student_count=student_count,
        teacher_count=teacher_count,
        course_count=sum(r.cnt for r in course_rows),
        majors=[CollegeOverviewMajor(id=r.id, name=r.name, student_count=r.cnt) for r in major_rows],
        classes=[CollegeOverviewClass(id=r.id, name=r.name, student_count=r.cnt) for r in class_rows],
        courses=[CollegeOverviewCourse(major_name=r.name, course_count=r.cnt) for r in course_rows],
    )
