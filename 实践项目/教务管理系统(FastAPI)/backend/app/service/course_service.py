"""课程与学期管理 Service"""
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.course_dao import semester_dao, course_dao
from app.model.course import Course
from app.model.semester import Semester
from app.dto.semester_schema import SemesterCreate, SemesterUpdate, SemesterResponse
from app.dto.course_schema import CourseCreate, CourseUpdate, CourseResponse, CoursePageQuery
from app.common.exception import NotFoundException


# ========== 学期管理 ==========

async def create_semester(db: AsyncSession, req: SemesterCreate) -> SemesterResponse:
    semester = Semester(name=req.name, start_date=req.start_date, end_date=req.end_date, is_current=req.is_current)
    semester = await semester_dao.create(db, semester)
    return SemesterResponse.model_validate(semester)

async def update_semester(db: AsyncSession, semester_id: int, req: SemesterUpdate) -> SemesterResponse:
    semester = await semester_dao.get_by_id(db, semester_id)
    if not semester:
        raise NotFoundException(f"学期不存在: id={semester_id}")
    semester = await semester_dao.update(db, semester, name=req.name, start_date=req.start_date, end_date=req.end_date, is_current=req.is_current)
    return SemesterResponse.model_validate(semester)

async def delete_semester(db: AsyncSession, semester_id: int) -> bool:
    if not await semester_dao.delete(db, semester_id):
        raise NotFoundException(f"学期不存在: id={semester_id}")
    return True

async def get_semester(db: AsyncSession, semester_id: int) -> SemesterResponse:
    semester = await semester_dao.get_by_id(db, semester_id)
    if not semester:
        raise NotFoundException(f"学期不存在: id={semester_id}")
    return SemesterResponse.model_validate(semester)

async def list_semesters(db: AsyncSession, page: int = 1, page_size: int = 20) -> tuple[list, int]:
    items, total = await semester_dao.get_all(db, page=page, page_size=page_size, order_by=Semester.id.desc())
    return [SemesterResponse.model_validate(s) for s in items], total

async def get_all_semesters(db: AsyncSession) -> list:
    items, _ = await semester_dao.get_all(db, page=1, page_size=100, order_by=Semester.id.desc())
    return [SemesterResponse.model_validate(s) for s in items]


# ========== 课程管理 ==========

async def create_course(db: AsyncSession, req: CourseCreate) -> CourseResponse:
    course = Course(code=req.code, name=req.name, semester_id=req.semester_id, college_id=req.college_id, teacher_id=req.teacher_id, credit=req.credit, max_capacity=req.max_capacity, hours=req.hours, type=req.type, category=req.category or '', description=req.description)
    course = await course_dao.create(db, course)
    return CourseResponse.model_validate(course)

async def update_course(db: AsyncSession, course_id: int, req: CourseUpdate) -> CourseResponse:
    course = await course_dao.get_by_id(db, course_id)
    if not course:
        raise NotFoundException(f"课程不存在: id={course_id}")
    course = await course_dao.update(db, course, name=req.name, teacher_id=req.teacher_id, credit=req.credit, max_capacity=req.max_capacity, hours=req.hours, type=req.type, category=req.category, description=req.description)
    return CourseResponse.model_validate(course)

async def delete_course(db: AsyncSession, course_id: int) -> bool:
    if not await course_dao.delete(db, course_id):
        raise NotFoundException(f"课程不存在: id={course_id}")
    return True

async def get_course(db: AsyncSession, course_id: int) -> CourseResponse:
    course = await course_dao.get_by_id(db, course_id)
    if not course:
        raise NotFoundException(f"课程不存在: id={course_id}")
    return CourseResponse.model_validate(course)

async def list_courses(db: AsyncSession, query: CoursePageQuery) -> tuple[list[CourseResponse], int]:
    filters = []
    if query.semester_id:
        filters.append(Course.semester_id == query.semester_id)
    if query.college_id:
        filters.append(Course.college_id == query.college_id)
    if query.teacher_id:
        filters.append(Course.teacher_id == query.teacher_id)
    if query.type:
        filters.append(Course.type == query.type)
    if query.category:
        filters.append(Course.category == query.category)
    if query.keyword:
        filters.append(or_(Course.name.like(f"%{query.keyword}%"), Course.code.like(f"%{query.keyword}%")))
    items, total = await course_dao.get_all(db, page=query.page, page_size=query.page_size, filters=filters, order_by=Course.code)
    return [CourseResponse.model_validate(c) for c in items], total


async def list_available_courses(db: AsyncSession, student_id: int, keyword: str = None, type: str = None, teacher_name: str = None, code: str = None) -> list[dict]:
    """获取学生本学期可选课程（排除已选/已满），支持筛选"""
    from app.model.course_selection import CourseSelection as CS
    from app.model.semester import Semester
    from app.model.teacher import Teacher
    from app.model.user import User

    # 找当前学期
    semester = (await db.execute(
        select(Semester).where(Semester.is_current == True)
    )).scalar_one_or_none()
    if not semester:
        return []

    # 已选课程ID
    selected = (await db.execute(
        select(CS.course_id).where(
            CS.student_id == student_id,
            CS.semester_id == semester.id,
            CS.status == 'selected'
        )
    )).scalars().all()
    selected_ids = set(selected)

    # 本学期可选课程：当前学期 + 未满员 + 学生未选
    query = (
        select(Course, User.real_name.label('teacher_name'))
        .join(Teacher, Course.teacher_id == Teacher.id)
        .join(User, Teacher.user_id == User.id)
        .where(
            Course.semester_id == semester.id,
            Course.selected_count < Course.max_capacity,
        )
    )
    if selected_ids:
        query = query.where(Course.id.notin_(selected_ids))
    if keyword:
        query = query.where(or_(Course.name.like(f"%{keyword}%"), Course.code.like(f"%{keyword}%")))
    if code:
        query = query.where(Course.code.like(f"%{code}%"))
    if type:
        query = query.where(Course.type == type)
    if teacher_name:
        query = query.where(User.real_name.like(f"%{teacher_name}%"))

    result = await db.execute(query)
    rows = result.all()

    return [{
        "id": c.id,
        "code": c.code,
        "name": c.name,
        "type": c.type,
        "credit": float(c.credit),
        "hours": c.hours,
        "teacher_name": teacher_name_str,
        "max_capacity": c.max_capacity,
        "selected_count": c.selected_count,
        "description": c.description,
        "semester_name": semester.name,
        "college_id": c.college_id,
    } for c, teacher_name_str in rows]
