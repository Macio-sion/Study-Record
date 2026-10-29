"""考勤 DAO"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.model.attendance import Attendance
from app.dao.base_dao import BaseDAO


class AttendanceDAO(BaseDAO[Attendance]):
    def __init__(self):
        super().__init__(Attendance)

    async def get_stats(self, db: AsyncSession, course_id: int = None, student_id: int = None) -> dict:
        """获取考勤统计数据"""
        query = select(Attendance)
        if course_id:
            query = query.where(Attendance.course_id == course_id)
        if student_id:
            query = query.where(Attendance.student_id == student_id)
        result = await db.execute(query)
        records = result.scalars().all()
        total = len(records)
        present = sum(1 for r in records if r.status == '出勤')
        absent = sum(1 for r in records if r.status == '缺勤')
        late = sum(1 for r in records if r.status == '迟到')
        leave = sum(1 for r in records if r.status in ('请假', '公假'))
        rate = round(present / total * 100, 1) if total > 0 else 0.0
        return {"total": total, "present": present, "absent": absent, "late": late, "leave": leave, "rate": rate}


attendance_dao = AttendanceDAO()
