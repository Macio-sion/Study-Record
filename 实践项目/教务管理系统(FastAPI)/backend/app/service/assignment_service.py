"""作业管理 Service"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.base_dao import BaseDAO
from app.model.assignment import Assignment
from app.model.assignment_submission import AssignmentSubmission
from app.dto.assignment_schema import AssignmentCreate, AssignmentUpdate, AssignmentResponse, AssignmentPageQuery, SubmissionCreate, SubmissionReview, SubmissionResponse
from app.common.exception import NotFoundException, BusinessException

_assignment_dao = BaseDAO(Assignment)
_submission_dao = BaseDAO(AssignmentSubmission)


async def create_assignment(db: AsyncSession, req: AssignmentCreate) -> AssignmentResponse:
    assignment = Assignment(course_id=req.course_id, teacher_id=req.teacher_id, title=req.title, content=req.content, deadline=req.deadline)
    assignment = await _assignment_dao.create(db, assignment)
    return AssignmentResponse.model_validate(assignment)


async def update_assignment(db: AsyncSession, assignment_id: int, req: AssignmentUpdate) -> AssignmentResponse:
    assignment = await _assignment_dao.get_by_id(db, assignment_id)
    if not assignment:
        raise NotFoundException(f"作业不存在: id={assignment_id}")
    assignment = await _assignment_dao.update(db, assignment, title=req.title, content=req.content, deadline=req.deadline)
    return AssignmentResponse.model_validate(assignment)


async def delete_assignment(db: AsyncSession, assignment_id: int) -> bool:
    if not await _assignment_dao.delete(db, assignment_id):
        raise NotFoundException(f"作业不存在: id={assignment_id}")
    return True


async def get_assignment(db: AsyncSession, assignment_id: int) -> AssignmentResponse:
    a = await _assignment_dao.get_by_id(db, assignment_id)
    if not a:
        raise NotFoundException(f"作业不存在: id={assignment_id}")
    return AssignmentResponse.model_validate(a)


async def list_assignments(db: AsyncSession, query: AssignmentPageQuery, teacher_id: int = None) -> tuple[list[dict], int]:
    from sqlalchemy import select, func, or_
    from app.model.course import Course
    from app.model.teacher import Teacher
    from app.model.user import User

    filters = []
    if query.course_id:
        filters.append(Assignment.course_id == query.course_id)
    if teacher_id:
        filters.append(Assignment.teacher_id == teacher_id)
    if hasattr(query, 'keyword') and query.keyword:
        filters.append(or_(
            Assignment.title.like(f"%{query.keyword}%"),
            Assignment.content.like(f"%{query.keyword}%"),
        ))

    # COUNT
    count_q = select(func.count(Assignment.id))
    if filters:
        count_q = count_q.where(*filters)
    total = (await db.execute(count_q)).scalar() or 0

    # JOIN 查询
    main_q = (
        select(
            Assignment,
            Course.name.label('course_name'),
            func.count(AssignmentSubmission.id).label('submission_count'),
            User.real_name.label('teacher_name'),
        )
        .join(Course, Assignment.course_id == Course.id)
        .join(Teacher, Assignment.teacher_id == Teacher.id)
        .join(User, Teacher.user_id == User.id)
        .outerjoin(AssignmentSubmission, AssignmentSubmission.assignment_id == Assignment.id)
        .group_by(Assignment.id, Course.name, User.real_name)
        .order_by(Assignment.deadline.desc())
        .limit(query.page_size).offset((query.page - 1) * query.page_size)
    )
    if filters:
        main_q = main_q.where(*filters)

    result = await db.execute(main_q)
    rows = result.all()

    return [{
        "id": a.id,
        "course_id": a.course_id,
        "teacher_id": a.teacher_id,
        "title": a.title,
        "content": a.content,
        "course_name": course_name,
        "teacher_name": teacher_name,
        "due_date": str(a.deadline),
        "submission_count": submission_count,
        "created_at": str(a.created_at),
        "updated_at": str(a.created_at),
    } for a, course_name, submission_count, teacher_name in rows], total


async def submit_assignment(db: AsyncSession, req: SubmissionCreate) -> SubmissionResponse:
    sub = AssignmentSubmission(assignment_id=req.assignment_id, student_id=req.student_id, content=req.content)
    sub = await _submission_dao.create(db, sub)
    return SubmissionResponse.model_validate(sub)


async def update_my_submission(db: AsyncSession, submission_id: int, student_id: int, req: SubmissionCreate) -> SubmissionResponse:
    """学生修改自己已提交但未批改的作业（修改申请）"""
    sub = await _submission_dao.get_by_id(db, submission_id)
    if not sub:
        raise NotFoundException(f"提交记录不存在: id={submission_id}")
    if sub.student_id != student_id:
        raise BusinessException(code=403, message="无权修改他人的提交")
    if sub.reviewed_at:
        raise BusinessException(code=400, message="作业已被批改，无法修改")
    sub = await _submission_dao.update(db, sub, content=req.content)
    return SubmissionResponse.model_validate(sub)


async def review_submission(db: AsyncSession, submission_id: int, req: SubmissionReview) -> SubmissionResponse:
    sub = await _submission_dao.get_by_id(db, submission_id)
    if not sub:
        raise NotFoundException(f"提交记录不存在: id={submission_id}")
    import datetime
    sub = await _submission_dao.update(db, sub, score=req.score, comment=req.comment, reviewed_at=datetime.datetime.now())
    return SubmissionResponse.model_validate(sub)


async def get_submission(db: AsyncSession, submission_id: int) -> SubmissionResponse:
    sub = await _submission_dao.get_by_id(db, submission_id)
    if not sub:
        raise NotFoundException(f"提交记录不存在: id={submission_id}")
    return SubmissionResponse.model_validate(sub)


async def list_submissions(db: AsyncSession, assignment_id: int, page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
    from sqlalchemy import select, func
    from app.model.student import Student
    from app.model.user import User

    # COUNT
    count_q = select(func.count(AssignmentSubmission.id)).where(AssignmentSubmission.assignment_id == assignment_id)
    total = (await db.execute(count_q)).scalar() or 0

    # JOIN 查询
    main_q = (
        select(AssignmentSubmission, User.real_name.label('student_name'), Student.student_no.label('student_no'))
        .join(Student, AssignmentSubmission.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .where(AssignmentSubmission.assignment_id == assignment_id)
        .order_by(AssignmentSubmission.submitted_at.desc())
        .limit(page_size).offset((page - 1) * page_size)
    )
    result = await db.execute(main_q)
    rows = result.all()

    return [{
        "id": s.id,
        "assignment_id": s.assignment_id,
        "student_id": s.student_id,
        "student_name": student_name,
        "student_no": student_no,
        "content": s.content,
        "file_path": s.file_path,
        "score": float(s.score) if s.score else None,
        "comment": s.comment,
        "status": s.status,
        "submitted_at": str(s.submitted_at),
        "reviewed_at": str(s.reviewed_at) if s.reviewed_at else None,
    } for s, student_name, student_no in rows], total


async def list_my_assignments(db: AsyncSession, student_id: int, page: int = 1, page_size: int = 20, course_id: int = None) -> tuple[list[dict], int]:
    """学生查看自己课程的作业（含提交状态）"""
    from sqlalchemy import select, func, and_
    from app.model.course_selection import CourseSelection
    from app.model.course import Course
    from app.model.teacher import Teacher
    from app.model.user import User

    # 获取学生所选课程
    cs_query = select(CourseSelection.course_id).where(
        CourseSelection.student_id == student_id,
        CourseSelection.status == 'selected'
    )
    if course_id:
        cs_query = cs_query.where(CourseSelection.course_id == course_id)
    course_ids = (await db.execute(cs_query)).scalars().all()
    if not course_ids:
        return [], 0

    # COUNT
    count_stmt = select(func.count(Assignment.id)).where(Assignment.course_id.in_(course_ids))
    total = (await db.execute(count_stmt)).scalar() or 0

    # 作业列表 + 课程名 + 教师名
    stmt = (
        select(Assignment, Course.name.label('course_name'), User.real_name.label('teacher_name'))
        .join(Course, Assignment.course_id == Course.id)
        .join(Teacher, Assignment.teacher_id == Teacher.id)
        .join(User, Teacher.user_id == User.id)
        .where(Assignment.course_id.in_(course_ids))
        .order_by(Assignment.deadline.desc())
        .limit(page_size).offset((page - 1) * page_size)
    )
    result = await db.execute(stmt)
    rows = result.all()

    # 批量查提交状态
    assignment_ids = [a.id for a, _, _ in rows]
    submissions_map = {}
    if assignment_ids:
        sub_stmt = select(AssignmentSubmission).where(
            AssignmentSubmission.assignment_id.in_(assignment_ids),
            AssignmentSubmission.student_id == student_id
        )
        subs = (await db.execute(sub_stmt)).scalars().all()
        for s in subs:
            submissions_map[s.assignment_id] = s

    items = []
    for a, course_name, teacher_name in rows:
        sub = submissions_map.get(a.id)
        if sub is None:
            sub_status = "未提交"
        elif sub.reviewed_at:
            sub_status = "已批改"
        else:
            sub_status = "已提交"
        items.append({
            "id": a.id,
            "title": a.title,
            "course_name": course_name,
            "teacher_name": teacher_name,
            "created_at": str(a.created_at),
            "deadline": str(a.deadline),
            "status": sub_status,
            "has_submission": sub is not None,
            "submission_id": sub.id if sub else None,
            "content": sub.content if sub else '',
            "score": float(sub.score) if sub and sub.score else None,
            "comment": sub.comment if sub else None,
        })
    return items, total
