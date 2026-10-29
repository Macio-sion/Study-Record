"""选课 DAO"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.model.course_selection import CourseSelection
from app.dao.base_dao import BaseDAO


class SelectionDAO(BaseDAO[CourseSelection]):
    def __init__(self):
        super().__init__(CourseSelection)

    async def check_exists(self, db: AsyncSession, student_id: int, course_id: int, semester_id: int) -> bool:
        result = await db.execute(
            select(CourseSelection).where(
                CourseSelection.student_id == student_id,
                CourseSelection.course_id == course_id,
                CourseSelection.semester_id == semester_id,
                CourseSelection.status == 'selected',
            )
        )
        return result.scalar_one_or_none() is not None


selection_dao = SelectionDAO()
