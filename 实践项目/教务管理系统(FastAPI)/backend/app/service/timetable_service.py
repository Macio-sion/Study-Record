"""课表 Service"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.model.schedule import Schedule
from app.model.course_selection import CourseSelection
from app.model.teacher import Teacher


async def get_student_timetable(db: AsyncSession, student_id: int, semester_id: int) -> list[dict]:
    """获取学生课表（通过选课记录关联排课）"""
    sel_result = await db.execute(
        select(CourseSelection.course_id)
        .where(CourseSelection.student_id == student_id, CourseSelection.semester_id == semester_id, CourseSelection.status == 'selected')
    )
    course_ids = [row[0] for row in sel_result.all()]
    if not course_ids:
        return []
    sched_result = await db.execute(
        select(Schedule)
        .options(
            selectinload(Schedule.course),
            selectinload(Schedule.classroom),
            selectinload(Schedule.teacher).selectinload(Teacher.user),
        )
        .where(Schedule.course_id.in_(course_ids), Schedule.semester_id == semester_id)
    )
    schedules = sched_result.scalars().all()
    return [_schedule_to_dict(s) for s in schedules]


async def get_teacher_timetable(db: AsyncSession, teacher_id: int, semester_id: int) -> list[dict]:
    """获取教师课表"""
    result = await db.execute(
        select(Schedule)
        .options(
            selectinload(Schedule.course),
            selectinload(Schedule.classroom),
            selectinload(Schedule.teacher).selectinload(Teacher.user),
        )
        .where(Schedule.teacher_id == teacher_id, Schedule.semester_id == semester_id)
    )
    schedules = result.scalars().all()
    return [_schedule_to_dict(s) for s in schedules]


async def get_all_timetable(db: AsyncSession, semester_id: int, week: int = None) -> list[dict]:
    """获取全部课表（管理员）"""
    stmt = select(Schedule).options(
        selectinload(Schedule.course),
        selectinload(Schedule.classroom),
        selectinload(Schedule.teacher).selectinload(Teacher.user),
    ).where(Schedule.semester_id == semester_id)
    if week is not None:
        stmt = stmt.where(Schedule.week_start <= week, Schedule.week_end >= week)
    result = await db.execute(stmt)
    schedules = result.scalars().all()
    return [_schedule_to_dict(s) for s in schedules]


def _schedule_to_dict(s: Schedule) -> dict:
    return {
        "id": s.id, "course_id": s.course_id, "classroom_id": s.classroom_id,
        "teacher_id": s.teacher_id, "semester_id": s.semester_id,
        "week_start": s.week_start, "week_end": s.week_end,
        "day_of_week": s.day_of_week, "period_start": s.period_start, "period_end": s.period_end,
        "course_name": s.course.name if s.course else "",
        "teacher_name": s.teacher.user.real_name if s.teacher and s.teacher.user else "",
        "classroom_name": s.classroom.name if s.classroom else "",
    }
