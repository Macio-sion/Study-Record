"""
Pytest 共享 fixtures
"""
import os
import sys

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from app.model.base import Base
from app.model import *  # noqa: F401,F403


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """每个测试独立的数据库引擎（避免Windows事件循环问题）"""
    engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def seed_data(db_session):
    """创建测试基础数据（使用自增ID，返回ID映射）"""
    from datetime import date
    from app.model.semester import Semester
    from app.model.college import College
    from app.model.major import Major
    from app.model.class_model import Class
    from app.model.user import User
    from app.model.teacher import Teacher
    from app.model.student import Student
    from app.model.course import Course
    from app.model.classroom import Classroom
    from app.common.security import hash_password

    # 学期
    sem = Semester(name="2026春季学期", start_date=date(2026, 3, 1), end_date=date(2026, 7, 15), is_current=True)
    db_session.add(sem)
    await db_session.flush()

    # 学院
    col = College(code="TEST_CS", name="测试计算机学院")
    db_session.add(col)
    await db_session.flush()

    # 专业
    maj = Major(code="TEST_CS001", name="测试专业", college_id=col.id, degree="工学学士")
    db_session.add(maj)
    await db_session.flush()

    # 班级
    cls = Class(class_no="TEST_CS2024", name="测试班级", major_id=maj.id, grade=2024)
    db_session.add(cls)
    await db_session.flush()

    # 教师用户
    teacher_user = User(username="test_teacher01", password_hash=hash_password("test"), real_name="测试教师", role_code="teacher", is_active=True)
    db_session.add(teacher_user)
    teacher_user2 = User(username="test_teacher02", password_hash=hash_password("test"), real_name="测试教师2", role_code="teacher", is_active=True)
    db_session.add(teacher_user2)
    await db_session.flush()

    # 学生用户
    student_user = User(username="test_student01", password_hash=hash_password("test"), real_name="测试学生", role_code="student", is_active=True)
    db_session.add(student_user)
    student_user2 = User(username="test_student02", password_hash=hash_password("test"), real_name="测试学生2", role_code="student", is_active=True)
    db_session.add(student_user2)
    await db_session.flush()

    # 教师
    t = Teacher(teacher_no="TEST_T001", user_id=teacher_user.id, college_id=col.id, gender="男", title="教授")
    db_session.add(t)
    t2 = Teacher(teacher_no="TEST_T002", user_id=teacher_user2.id, college_id=col.id, gender="女", title="副教授")
    db_session.add(t2)
    await db_session.flush()

    # 学生
    s1 = Student(student_no="TEST_S001", user_id=student_user.id, major_id=maj.id, class_id=cls.id, gender="男", enrollment_year=2024)
    s2 = Student(student_no="TEST_S002", user_id=student_user2.id, major_id=maj.id, class_id=cls.id, gender="女", enrollment_year=2024)
    db_session.add(s1)
    db_session.add(s2)
    await db_session.flush()

    # 教室
    cr1 = Classroom(room_no="TEST_R101", name="101教室", building="教学楼A", capacity=100, type="多媒体")
    cr2 = Classroom(room_no="TEST_R102", name="102教室", building="教学楼A", capacity=60, type="普通")
    db_session.add(cr1)
    db_session.add(cr2)
    await db_session.flush()

    # 课程（c1归teacher1，c2归teacher2）
    c1 = Course(code="TEST_C001", name="测试数据结构", semester_id=sem.id, college_id=col.id, teacher_id=t.id, credit=4, max_capacity=50, selected_count=0, hours=64, type="必修")
    c2 = Course(code="TEST_C002", name="测试操作系统", semester_id=sem.id, college_id=col.id, teacher_id=t2.id, credit=3, max_capacity=50, selected_count=0, hours=48, type="必修")
    db_session.add(c1)
    db_session.add(c2)
    await db_session.flush()

    return {
        "semester_id": sem.id, "college_id": col.id, "major_id": maj.id, "class_id": cls.id,
        "teacher_id": t.id, "teacher2_id": t2.id, "teacher_user_id": teacher_user.id,
        "student_id": s1.id, "student2_id": s2.id, "student_user_id": student_user.id, "student_user2_id": student_user2.id,
        "course_id": c1.id, "course2_id": c2.id,
        "classroom_id": cr1.id, "classroom2_id": cr2.id,
    }


@pytest_asyncio.fixture
async def admin_token():
    from app.common.security import create_access_token
    return create_access_token({"sub": "99", "username": "admin", "role": "admin"})


@pytest_asyncio.fixture
async def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
