"""考勤管理 Service"""
from sqlalchemy import or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.attendance_dao import attendance_dao
from app.model.attendance import Attendance
from app.dto.attendance_schema import AttendanceCreate, AttendanceUpdate, AttendanceResponse, AttendancePageQuery, AttendanceStatsResponse
from app.common.exception import NotFoundException, BusinessException


async def create_attendance(db: AsyncSession, req: AttendanceCreate) -> AttendanceResponse:
    """创建点名记录"""
    attendance = Attendance(course_id=req.course_id, student_id=req.student_id, teacher_id=req.teacher_id, date=req.date, status=req.status, remark=req.remark)
    attendance = await attendance_dao.create(db, attendance)
    return AttendanceResponse.model_validate(attendance)


async def batch_create_attendance(db: AsyncSession, records: list[AttendanceCreate]) -> list[AttendanceResponse]:
    """批量点名"""
    results = []
    for req in records:
        attendance = Attendance(course_id=req.course_id, student_id=req.student_id, teacher_id=req.teacher_id, date=req.date, status=req.status, remark=req.remark)
        db.add(attendance)
        results.append(attendance)
    await db.flush()
    return [AttendanceResponse.model_validate(a) for a in results]


async def update_attendance(db: AsyncSession, attendance_id: int, req: AttendanceUpdate) -> AttendanceResponse:
    attendance = await attendance_dao.get_by_id(db, attendance_id)
    if not attendance:
        raise NotFoundException(f"考勤记录不存在: id={attendance_id}")
    attendance = await attendance_dao.update(db, attendance, status=req.status, remark=req.remark)
    return AttendanceResponse.model_validate(attendance)


async def delete_attendance(db: AsyncSession, attendance_id: int) -> bool:
    if not await attendance_dao.delete(db, attendance_id):
        raise NotFoundException(f"考勤记录不存在: id={attendance_id}")
    return True


async def get_attendance(db: AsyncSession, attendance_id: int) -> AttendanceResponse:
    attendance = await attendance_dao.get_by_id(db, attendance_id)
    if not attendance:
        raise NotFoundException(f"考勤记录不存在: id={attendance_id}")
    return AttendanceResponse.model_validate(attendance)


async def list_attendance(db: AsyncSession, query: AttendancePageQuery) -> tuple[list[dict], int]:
    from sqlalchemy import select, func
    from app.model.course import Course
    from app.model.student import Student
    from app.model.user import User

    filters = []
    if query.course_id:
        filters.append(Attendance.course_id == query.course_id)
    if query.student_id:
        filters.append(Attendance.student_id == query.student_id)
    if query.date:
        filters.append(Attendance.date == query.date)
    if query.status:
        filters.append(Attendance.status == query.status)

    # COUNT
    count_q = select(func.count()).select_from(Attendance)
    if filters:
        count_q = count_q.where(*filters)
    total = (await db.execute(count_q)).scalar() or 0

    # JOIN 查询
    main_q = (
        select(Attendance, Course.name.label('course_name'),
               User.real_name.label('student_name'), Student.student_no.label('student_no'))
        .join(Course, Attendance.course_id == Course.id)
        .join(Student, Attendance.student_id == Student.id)
        .join(User, Student.user_id == User.id)
    )
    if filters:
        main_q = main_q.where(*filters)
    main_q = main_q.order_by(Attendance.date.desc()).limit(query.page_size).offset((query.page - 1) * query.page_size)
    result = await db.execute(main_q)
    rows = result.all()

    return [{
        "id": a.id,
        "course_id": a.course_id,
        "student_id": a.student_id,
        "teacher_id": a.teacher_id,
        "date": str(a.date),
        "status": a.status,
        "remark": a.remark,
        "course_name": course_name,
        "student_name": student_name,
        "student_no": student_no,
        "created_at": str(a.created_at),
        "updated_at": str(a.updated_at),
    } for a, course_name, student_name, student_no in rows], total


async def get_attendance_stats(db: AsyncSession, course_id: int = None, student_id: int = None) -> AttendanceStatsResponse:
    """获取考勤统计"""
    stats = await attendance_dao.get_stats(db, course_id, student_id)
    return AttendanceStatsResponse(**stats)


async def list_my_attendance(db: AsyncSession, query: AttendancePageQuery) -> tuple[list[dict], int]:
    """学生查看自己的考勤（按日期降序，JOIN课程名）"""
    from sqlalchemy import select, func
    from app.model.course import Course

    filters = [Attendance.student_id == query.student_id]
    if query.date:
        filters.append(Attendance.date == query.date)
    if query.status:
        filters.append(Attendance.status == query.status)
    if query.course_id:
        filters.append(Attendance.course_id == query.course_id)

    # COUNT
    count_stmt = select(func.count(Attendance.id)).where(and_(*filters))
    total = (await db.execute(count_stmt)).scalar() or 0

    # 查询并 JOIN 课程名
    stmt = (
        select(Attendance, Course.name.label('course_name'))
        .join(Course, Attendance.course_id == Course.id)
        .where(and_(*filters))
        .order_by(Attendance.date.desc())
        .limit(query.page_size).offset((query.page - 1) * query.page_size)
    )
    result = await db.execute(stmt)
    rows = result.all()
    items = [{
        "id": a.id,
        "course_name": course_name,
        "date": str(a.date),
        "status": a.status,
        "remark": a.remark,
        "created_at": str(a.created_at),
    } for a, course_name in rows]
    return items, total


async def get_courses_stats(db: AsyncSession, course_ids: list[int]) -> list[dict]:
    """获取指定多门课程的出勤统计"""
    from sqlalchemy import select, func
    from app.model.course import Course

    if not course_ids:
        return []

    result = []
    for cid in course_ids:
        # 查课程名
        cq = await db.execute(select(Course.name).where(Course.id == cid))
        cname = cq.scalar()
        if not cname:
            continue
        att_q = await db.execute(
            select(Attendance.status).where(Attendance.course_id == cid)
        )
        records = att_q.scalars().all()
        total = len(records)
        present = sum(1 for r in records if r == '出勤')
        absent = sum(1 for r in records if r == '缺勤')
        late = sum(1 for r in records if r == '迟到')
        leave = sum(1 for r in records if r in ('请假', '公假'))
        rate = round(present / total * 100, 1) if total > 0 else 0.0
        result.append({
            "course_id": cid,
            "course_name": cname,
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "leave": leave,
            "rate": rate,
        })
    return result


async def get_teacher_course_stats(db: AsyncSession, teacher_id: int) -> list[dict]:
    """获取教师所授各课程的出勤统计"""
    from sqlalchemy import select, func
    from app.model.course import Course

    # 查所有课程
    course_q = await db.execute(
        select(Course.id, Course.name).where(Course.teacher_id == teacher_id)
    )
    courses = course_q.all()

    result = []
    for cid, cname in courses:
        att_q = await db.execute(
            select(Attendance.status).where(Attendance.course_id == cid)
        )
        records = att_q.scalars().all()
        total = len(records)
        present = sum(1 for r in records if r == '出勤')
        absent = sum(1 for r in records if r == '缺勤')
        late = sum(1 for r in records if r == '迟到')
        leave = sum(1 for r in records if r in ('请假', '公假'))
        rate = round(present / total * 100, 1) if total > 0 else 0.0
        result.append({
            "course_id": cid,
            "course_name": cname,
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "leave": leave,
            "rate": rate,
        })
    return result
