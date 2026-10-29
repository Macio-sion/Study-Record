"""请假管理 Service — 两级审批"""
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.leave_dao import leave_dao
from app.dao.course_dao import course_dao
from app.model.leave_request import LeaveRequest
from app.model.student import Student
from app.model.teacher import Teacher
from app.dto.leave_schema import LeaveCreate, LeaveUpdate, LeaveResponse, LeavePageQuery
from app.common.exception import NotFoundException, BusinessException


async def _get_student_by_user_id(db: AsyncSession, user_id: int) -> Student:
    result = await db.execute(select(Student).where(Student.user_id == user_id))
    student = result.scalar_one_or_none()
    if not student:
        raise BusinessException(message="当前用户未关联学生档案")
    return student


async def _get_teacher_by_user_id(db: AsyncSession, user_id: int) -> Teacher:
    result = await db.execute(select(Teacher).where(Teacher.user_id == user_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise BusinessException(message="当前用户未关联教师档案")
    return teacher


VALID_LEAVE_TYPES = {'病假', '事假', '公假', '其他'}


async def create_leave(db: AsyncSession, user_id: int, req: LeaveCreate) -> LeaveResponse:
    """提交请假申请"""
    if req.leave_type not in VALID_LEAVE_TYPES:
        raise BusinessException(message=f"无效的请假类型: {req.leave_type}")
    student = await _get_student_by_user_id(db, user_id)
    course = await course_dao.get_by_id(db, req.course_id)
    if not course:
        raise NotFoundException(f"课程不存在: id={req.course_id}")
    leave = LeaveRequest(
        student_id=student.id, course_id=req.course_id,
        leave_type=req.leave_type, leave_date=req.leave_date, reason=req.reason,
        status='pending_teacher',
    )
    leave = await leave_dao.create(db, leave)
    return LeaveResponse.model_validate(leave)


async def approve_teacher(db: AsyncSession, leave_id: int, user_id: int, req: LeaveUpdate) -> LeaveResponse:
    """任课教师审批（第一级）"""
    teacher = await _get_teacher_by_user_id(db, user_id)
    leave = await leave_dao.get_by_id(db, leave_id)
    if not leave:
        raise NotFoundException(f"请假记录不存在: id={leave_id}")
    if leave.status != 'pending_teacher':
        raise BusinessException(message="该请假申请当前状态不允许教师审批")
    leave.teacher_id = teacher.id
    leave.teacher_opinion = req.opinion
    leave.teacher_at = datetime.now()
    leave.status = 'pending_staff' if req.approved else 'rejected'
    leave = await leave_dao.update(db, leave, **{
        'teacher_id': teacher.id, 'teacher_opinion': req.opinion,
        'teacher_at': leave.teacher_at, 'status': leave.status,
    })
    return LeaveResponse.model_validate(leave)


async def approve_staff(db: AsyncSession, leave_id: int, staff_user_id: int, req: LeaveUpdate) -> LeaveResponse:
    """学工处审批（第二级）— staff_user_id 直接使用 users.id"""
    leave = await leave_dao.get_by_id(db, leave_id)
    if not leave:
        raise NotFoundException(f"请假记录不存在: id={leave_id}")
    if leave.status != 'pending_staff':
        raise BusinessException(message="该请假申请当前状态不允许学工处审批")
    leave.staff_id = staff_user_id
    leave.staff_opinion = req.opinion
    leave.staff_at = datetime.now()
    leave.status = 'approved' if req.approved else 'rejected'
    leave = await leave_dao.update(db, leave, **{
        'staff_id': staff_user_id, 'staff_opinion': req.opinion,
        'staff_at': leave.staff_at, 'status': leave.status,
    })
    return LeaveResponse.model_validate(leave)


async def cancel_leave(db: AsyncSession, leave_id: int, user_id: int) -> LeaveResponse:
    """学生撤销请假申请（仅pending状态可撤销）"""
    student = await _get_student_by_user_id(db, user_id)
    leave = await leave_dao.get_by_id(db, leave_id)
    if not leave:
        raise NotFoundException(f"请假记录不存在: id={leave_id}")
    if leave.student_id != student.id:
        raise BusinessException(message="只能撤销自己的请假申请")
    if leave.status not in ('pending_teacher', 'pending_staff'):
        raise BusinessException(message="当前状态不允许撤销")
    leave.status = 'cancelled'
    leave = await leave_dao.update(db, leave, status='cancelled')
    return LeaveResponse.model_validate(leave)


async def get_leave(db: AsyncSession, leave_id: int) -> LeaveResponse:
    leave = await leave_dao.get_by_id(db, leave_id)
    if not leave:
        raise NotFoundException(f"请假记录不存在: id={leave_id}")
    return LeaveResponse.model_validate(leave)


async def list_leaves(db: AsyncSession, query: LeavePageQuery, teacher_id: int = None) -> tuple[list[dict], int]:
    from sqlalchemy import or_, func
    from app.model.course import Course
    from app.model.course_selection import CourseSelection
    from app.model.user import User
    filters = []
    if query.student_id:
        filters.append(LeaveRequest.student_id == query.student_id)
    if query.course_id:
        filters.append(LeaveRequest.course_id == query.course_id)
    if query.status:
        filters.append(LeaveRequest.status == query.status)
    if query.teacher_id:
        filters.append(LeaveRequest.teacher_id == query.teacher_id)
    if hasattr(query, 'keyword') and query.keyword:
        filters.append(or_(
            LeaveRequest.reason.like(f"%{query.keyword}%"),
            LeaveRequest.leave_type.like(f"%{query.keyword}%"),
        ))
    # 教师角色：只看自己所教课程中学生的请假
    if teacher_id:
        teacher_student_ids = (
            select(CourseSelection.student_id)
            .join(Course, CourseSelection.course_id == Course.id)
            .where(Course.teacher_id == teacher_id)
            .distinct()
        )
        filters.append(LeaveRequest.student_id.in_(teacher_student_ids))

    # 总数
    count_q = select(func.count()).select_from(LeaveRequest)
    if filters:
        count_q = count_q.where(*filters)
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # 分页 + JOIN 课程/学生
    main_q = (
        select(LeaveRequest, Course.name.label('course_name'), User.real_name.label('student_name'))
        .join(Course, LeaveRequest.course_id == Course.id)
        .join(Student, LeaveRequest.student_id == Student.id)
        .join(User, Student.user_id == User.id)
    )
    if filters:
        main_q = main_q.where(*filters)
    main_q = main_q.order_by(Course.name.asc()).offset((query.page - 1) * query.page_size).limit(query.page_size)
    result = await db.execute(main_q)
    rows = result.all()

    return [{
        "id": l.id, "student_id": l.student_id, "student_name": student_name,
        "course_id": l.course_id, "course_name": course_name,
        "leave_type": l.leave_type, "leave_date": l.leave_date,
        "reason": l.reason, "status": l.status,
        "teacher_id": l.teacher_id, "teacher_opinion": l.teacher_opinion,
        "teacher_at": l.teacher_at.isoformat() if l.teacher_at else None,
        "staff_id": l.staff_id, "staff_opinion": l.staff_opinion,
        "staff_at": l.staff_at.isoformat() if l.staff_at else None,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    } for l, course_name, student_name in rows], total
