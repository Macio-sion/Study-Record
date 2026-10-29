"""排课 DAO"""
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.model.schedule import Schedule
from app.dao.base_dao import BaseDAO


class ScheduleDAO(BaseDAO[Schedule]):
    def __init__(self):
        super().__init__(Schedule)

    async def check_conflict(self, db: AsyncSession, classroom_id: int, semester_id: int, week_start: int, week_end: int, day_of_week: int, period_start: int, period_end: int, exclude_id: int = None) -> bool:
        """检查教室时间冲突：同一教室、同一学期、同一时间段不能排两门课"""
        for w in range(week_start, week_end + 1):
            query = select(Schedule).where(
                and_(
                    Schedule.classroom_id == classroom_id,
                    Schedule.semester_id == semester_id,
                    Schedule.week_start <= w,
                    Schedule.week_end >= w,
                    Schedule.day_of_week == day_of_week,
                    Schedule.period_start < period_end,
                    Schedule.period_end > period_start,
                )
            )
            if exclude_id:
                query = query.where(Schedule.id != exclude_id)
            result = await db.execute(query)
            if result.scalar_one_or_none():
                return True
        return False

    async def get_teacher_conflict(self, db: AsyncSession, teacher_id: int, semester_id: int, week_start: int, week_end: int, day_of_week: int, period_start: int, period_end: int, exclude_id: int = None) -> bool:
        """检查教师时间冲突"""
        for w in range(week_start, week_end + 1):
            query = select(Schedule).where(
                and_(
                    Schedule.teacher_id == teacher_id,
                    Schedule.semester_id == semester_id,
                    Schedule.week_start <= w,
                    Schedule.week_end >= w,
                    Schedule.day_of_week == day_of_week,
                    Schedule.period_start < period_end,
                    Schedule.period_end > period_start,
                )
            )
            if exclude_id:
                query = query.where(Schedule.id != exclude_id)
            result = await db.execute(query)
            if result.scalar_one_or_none():
                return True
        return False


schedule_dao = ScheduleDAO()
