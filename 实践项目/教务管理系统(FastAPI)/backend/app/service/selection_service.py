"""选课管理 Service（高并发：乐观锁 + Redis限流）"""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.selection_dao import selection_dao
from app.dao.course_dao import course_dao
from app.model.course import Course
from app.model.course_selection import CourseSelection
from app.dto.selection_schema import CourseSelectionCreate, SelectionResponse, SelectionPageQuery
from app.common.exception import NotFoundException, BusinessException
from app.utils.rate_limiter import rate_limiter


async def select_course(db: AsyncSession, req: CourseSelectionCreate) -> SelectionResponse:
    """选课（含乐观锁、限流、重复检测）"""
    # 限流检查
    key = f"select_limit:{req.student_id}"
    if not rate_limiter(key, max_requests=10, window=1):
        raise BusinessException(code=429, message="操作过于频繁，请稍后再试")

    # 课程存在性
    course = await course_dao.get_by_id(db, req.course_id)
    if not course:
        raise NotFoundException(f"课程不存在: id={req.course_id}")

    # 已选检查
    if await selection_dao.check_exists(db, req.student_id, req.course_id, req.semester_id):
        raise BusinessException(code=409, message="您已选择该课程")

    # 容量检查 + 乐观锁更新
    if course.selected_count >= course.max_capacity:
        raise BusinessException(code=409, message="课程容量已满")

    result = await db.execute(
        update(Course)
        .where(Course.id == req.course_id, Course.version == course.version, Course.selected_count < Course.max_capacity)
        .values(selected_count=Course.selected_count + 1, version=Course.version + 1)
    )
    if result.rowcount == 0:
        raise BusinessException(code=409, message="选课失败，课程容量可能已被抢完，请刷新重试")

    selection = CourseSelection(student_id=req.student_id, course_id=req.course_id, semester_id=req.semester_id)
    selection = await selection_dao.create(db, selection)
    return SelectionResponse.model_validate(selection)


async def drop_course(db: AsyncSession, selection_id: int) -> bool:
    """退课（恢复课程容量）"""
    selection = await selection_dao.get_by_id(db, selection_id)
    if not selection:
        raise NotFoundException(f"选课记录不存在: id={selection_id}")
    if selection.status == 'dropped':
        raise BusinessException(code=409, message="该课程已退选")

    selection.status = 'dropped'
    await db.flush()

    # 恢复容量
    await db.execute(
        update(Course).where(Course.id == selection.course_id, Course.selected_count > 0)
        .values(selected_count=Course.selected_count - 1)
    )
    return True


async def get_selection(db: AsyncSession, selection_id: int) -> SelectionResponse:
    selection = await selection_dao.get_by_id(db, selection_id)
    if not selection:
        raise NotFoundException(f"选课记录不存在: id={selection_id}")
    return SelectionResponse.model_validate(selection)


async def list_selections(db: AsyncSession, query: SelectionPageQuery) -> tuple[list[dict], int]:
    from sqlalchemy import select, func
    from app.model.course_selection import CourseSelection as CS
    from app.model.course import Course
    from app.model.semester import Semester
    from app.model.student import Student
    from app.model.teacher import Teacher
    from app.model.major import Major
    from app.model.user import User

    filters = []
    if query.student_id:
        filters.append(CS.student_id == query.student_id)
    if query.course_id:
        filters.append(CS.course_id == query.course_id)
    if query.semester_id:
        filters.append(CS.semester_id == query.semester_id)
    if query.status:
        filters.append(CS.status == query.status)

    # 学院/专业筛选：JOIN Student → Major
    college_major_join = False
    if query.college_id or query.major_id:
        college_major_join = True

    # COUNT
    count_q = select(func.count()).select_from(CS)
    if college_major_join:
        count_q = count_q.join(Student, CS.student_id == Student.id).join(Major, Student.major_id == Major.id)
        if query.college_id:
            count_q = count_q.where(Major.college_id == query.college_id)
        if query.major_id:
            count_q = count_q.where(Student.major_id == query.major_id)
    if filters:
        count_q = count_q.where(*filters)
    total = (await db.execute(count_q)).scalar() or 0

    # JOIN 查询
    main_q = (
        select(CS, Course.code.label('course_code'), Course.name.label('course_name'),
               Course.type.label('course_type'), Course.credit.label('course_credit'),
               Semester.name.label('semester_name'),
               User.real_name.label('student_name'))
        .join(Course, CS.course_id == Course.id)
        .join(Semester, CS.semester_id == Semester.id)
        .join(Student, CS.student_id == Student.id)
        .join(User, Student.user_id == User.id)
    )
    if college_major_join:
        main_q = main_q.join(Major, Student.major_id == Major.id)
        if query.college_id:
            main_q = main_q.where(Major.college_id == query.college_id)
        if query.major_id:
            main_q = main_q.where(Student.major_id == query.major_id)
    if filters:
        main_q = main_q.where(*filters)
    main_q = main_q.order_by(CS.id.desc()).offset((query.page - 1) * query.page_size).limit(query.page_size)
    result = await db.execute(main_q)
    rows = result.all()

    # 批量查教师名
    course_ids = [cs.course_id for cs, *_ in rows]
    teacher_map = {}
    if course_ids:
        t_q = select(Course.id, User.real_name).join(Teacher, Course.teacher_id == Teacher.id).join(User, Teacher.user_id == User.id).where(Course.id.in_(course_ids))
        t_res = await db.execute(t_q)
        for cid, tname in t_res.all():
            teacher_map[cid] = tname

    return [{
        "id": cs.id,
        "student_id": cs.student_id,
        "course_id": cs.course_id,
        "semester_id": cs.semester_id,
        "selected_at": cs.selected_at.isoformat() if cs.selected_at else None,
        "status": cs.status,
        "student_name": s_name,
        "course_code": c_code,
        "course_name": c_name,
        "course_type": c_type,
        "course_credit": float(c_credit) if c_credit else 0,
        "teacher_name": teacher_map.get(cs.course_id, ''),
        "semester_name": sem_name,
    } for cs, c_code, c_name, c_type, c_credit, sem_name, s_name in rows], total


async def get_student_courses(db: AsyncSession, student_id: int, semester_id: int = None):
    """获取学生的选课列表（含课程信息）"""
    from app.model.course_selection import CourseSelection as CS
    from app.model.course import Course
    from app.dto.course_schema import CourseResponse

    query = select(Course).join(CS, CS.course_id == Course.id).where(
        CS.student_id == student_id,
        CS.status == 'selected',
    )
    if semester_id:
        query = query.where(CS.semester_id == semester_id)

    result = await db.execute(query)
    courses = result.scalars().all()
    return [CourseResponse.model_validate(c) for c in courses]
