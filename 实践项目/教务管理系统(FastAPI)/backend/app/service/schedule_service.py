"""排课管理 Service"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.schedule_dao import schedule_dao
from app.dao.course_dao import course_dao
from app.dao.college_dao import college_dao
from app.dao.classroom_dao import classroom_dao
from app.model.schedule import Schedule
from app.model.classroom import Classroom
from app.model.course import Course
from app.model.teacher import Teacher
from app.model.user import User
from app.model.semester import Semester
from app.dto.schedule_schema import ScheduleCreate, ScheduleUpdate, ScheduleResponse, SchedulePageQuery
from app.common.exception import NotFoundException, BusinessException


async def auto_assign_classroom(db: AsyncSession, semester_id: int, max_capacity: int, week_start: int, week_end: int, day_of_week: int, period_start: int, period_end: int, exclude_schedule_id: int = None) -> int:
    """自动匹配最佳教室：容量足够、状态可用、无时间冲突，返回教室ID"""
    # 查询所有可用教室，按容量升序（优先匹配最小够用的）
    result = await db.execute(
        select(Classroom).where(
            Classroom.status == '可用',
            Classroom.capacity >= max_capacity,
        ).order_by(Classroom.capacity.asc())
    )
    classrooms = result.scalars().all()

    if not classrooms:
        raise BusinessException(code=409, message=f"无可用教室满足容量需求(≥{max_capacity}人)")

    for room in classrooms:
        # 检查该教室在目标时间段是否冲突
        has_conflict = await schedule_dao.check_conflict(
            db, room.id, semester_id, week_start, week_end,
            day_of_week, period_start, period_end, exclude_id=exclude_schedule_id
        )
        if not has_conflict:
            return room.id

    raise BusinessException(code=409, message="所有满足容量的教室在目标时间段均有冲突")


async def create_schedule(db: AsyncSession, req: ScheduleCreate) -> ScheduleResponse:
    """创建排课，含冲突检测"""
    # 校验课程存在
    course = await course_dao.get_by_id(db, req.course_id)
    if not course:
        raise NotFoundException(f"课程不存在: id={req.course_id}")

    # 检查教室冲突
    if await schedule_dao.check_conflict(db, req.classroom_id, req.semester_id, req.week_start, req.week_end, req.day_of_week, req.period_start, req.period_end):
        raise BusinessException(code=409, message="该教室在指定时间段已被占用")

    # 检查教师冲突
    if await schedule_dao.get_teacher_conflict(db, req.teacher_id, req.semester_id, req.week_start, req.week_end, req.day_of_week, req.period_start, req.period_end):
        raise BusinessException(code=409, message="该教师在指定时间段已有课程安排")

    schedule = Schedule(
        course_id=req.course_id, classroom_id=req.classroom_id, teacher_id=req.teacher_id,
        semester_id=req.semester_id, week_start=req.week_start, week_end=req.week_end,
        day_of_week=req.day_of_week, period_start=req.period_start, period_end=req.period_end,
    )
    schedule = await schedule_dao.create(db, schedule)
    return ScheduleResponse.model_validate(schedule)


async def update_schedule(db: AsyncSession, schedule_id: int, req: ScheduleUpdate) -> ScheduleResponse:
    """更新排课"""
    schedule = await schedule_dao.get_by_id(db, schedule_id)
    if not schedule:
        raise NotFoundException(f"排课记录不存在: id={schedule_id}")
    # 用旧值填充未修改字段做冲突检测
    classroom_id = req.classroom_id or schedule.classroom_id
    week_start = req.week_start or schedule.week_start
    week_end = req.week_end or schedule.week_end
    day_of_week = req.day_of_week if req.day_of_week is not None else schedule.day_of_week
    period_start = req.period_start if req.period_start is not None else schedule.period_start
    period_end = req.period_end if req.period_end is not None else schedule.period_end
    if await schedule_dao.check_conflict(db, classroom_id, schedule.semester_id, week_start, week_end, day_of_week, period_start, period_end, exclude_id=schedule_id):
        raise BusinessException(code=409, message="该教室在指定时间段已被占用")
    schedule = await schedule_dao.update(db, schedule, classroom_id=req.classroom_id, week_start=req.week_start, week_end=req.week_end, day_of_week=req.day_of_week, period_start=req.period_start, period_end=req.period_end)
    return ScheduleResponse.model_validate(schedule)


async def delete_schedule(db: AsyncSession, schedule_id: int) -> bool:
    if not await schedule_dao.delete(db, schedule_id):
        raise NotFoundException(f"排课记录不存在: id={schedule_id}")
    return True


async def get_schedule(db: AsyncSession, schedule_id: int) -> ScheduleResponse:
    schedule = await schedule_dao.get_by_id(db, schedule_id)
    if not schedule:
        raise NotFoundException(f"排课记录不存在: id={schedule_id}")
    return ScheduleResponse.model_validate(schedule)


async def list_schedules(db: AsyncSession, query: SchedulePageQuery) -> tuple[list[ScheduleResponse], int]:
    filters = []
    if query.semester_id:
        filters.append(Schedule.semester_id == query.semester_id)
    if query.teacher_id:
        filters.append(Schedule.teacher_id == query.teacher_id)
    if query.classroom_id:
        filters.append(Schedule.classroom_id == query.classroom_id)

    count_q = select(func.count(Schedule.id))
    if filters:
        count_q = count_q.where(*filters)
    total = (await db.execute(count_q)).scalar() or 0

    main_q = (
        select(Schedule, Course.name.label('course_name'), User.real_name.label('teacher_name'),
               Classroom.name.label('classroom_name'), Semester.name.label('semester_name'))
        .join(Course, Schedule.course_id == Course.id)
        .join(Teacher, Schedule.teacher_id == Teacher.id)
        .join(User, Teacher.user_id == User.id)
        .join(Classroom, Schedule.classroom_id == Classroom.id)
        .join(Semester, Schedule.semester_id == Semester.id)
        .order_by(Schedule.id.desc())
        .limit(query.page_size).offset((query.page - 1) * query.page_size)
    )
    if filters:
        main_q = main_q.where(*filters)

    result = await db.execute(main_q)
    rows = result.all()

    return [ScheduleResponse(
        id=s.id, course_id=s.course_id, classroom_id=s.classroom_id, teacher_id=s.teacher_id,
        semester_id=s.semester_id, course_name=course_name, teacher_name=teacher_name,
        classroom_name=classroom_name, semester_name=semester_name,
        week_range=f"第{s.week_start}-{s.week_end}周",
        week_start=s.week_start, week_end=s.week_end,
        day_of_week=s.day_of_week, period_start=s.period_start, period_end=s.period_end,
        created_at=s.created_at,
    ) for s, course_name, teacher_name, classroom_name, semester_name in rows], total
