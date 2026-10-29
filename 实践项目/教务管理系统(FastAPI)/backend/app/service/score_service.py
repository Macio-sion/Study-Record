"""成绩管理 Service"""
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.score_dao import score_dao
from app.model.score import Score
from app.dto.score_schema import ScoreCreate, ScoreUpdate, ScoreResponse, ScorePageQuery
from app.common.exception import NotFoundException


async def create_score(db: AsyncSession, operator_id: int, req: ScoreCreate) -> ScoreResponse:
    score = Score(student_id=req.student_id, course_id=req.course_id, semester_id=req.semester_id, teacher_id=req.teacher_id, score=req.score)
    score = await score_dao.create(db, score)
    return ScoreResponse.model_validate(score)


async def update_score(db: AsyncSession, operator_id: int, score_id: int, req: ScoreUpdate) -> ScoreResponse:
    score = await score_dao.get_by_id(db, score_id)
    if not score:
        raise NotFoundException(f"成绩不存在: id={score_id}")
    old_score = score.score
    score = await score_dao.update(db, score, score=req.score)
    await score_dao.log_change(db, score_id, old_score, req.score, operator_id)
    return ScoreResponse.model_validate(score)


async def get_score(db: AsyncSession, score_id: int) -> ScoreResponse:
    score = await score_dao.get_by_id(db, score_id)
    if not score:
        raise NotFoundException(f"成绩不存在: id={score_id}")
    return ScoreResponse.model_validate(score)


async def list_scores(db: AsyncSession, query: ScorePageQuery) -> tuple[list[dict], int]:
    from sqlalchemy import select, func
    from app.model.course import Course
    from app.model.semester import Semester
    from app.model.student import Student
    from app.model.major import Major
    from app.model.user import User

    filters = []
    if query.student_id:
        filters.append(Score.student_id == query.student_id)
    if query.course_id:
        filters.append(Score.course_id == query.course_id)
    if query.semester_id:
        filters.append(Score.semester_id == query.semester_id)

    # COUNT
    count_q = select(func.count()).select_from(Score)
    if query.college_id or query.major_id:
        count_q = count_q.join(Student, Score.student_id == Student.id).join(Major, Student.major_id == Major.id)
        if query.college_id:
            count_q = count_q.where(Major.college_id == query.college_id)
        if query.major_id:
            count_q = count_q.where(Student.major_id == query.major_id)
    if query.keyword:
        count_q = count_q.join(Student, Score.student_id == Student.id).join(User, Student.user_id == User.id)
        count_q = count_q.where(or_(
            Student.student_no.like(f"%{query.keyword}%"),
            User.real_name.like(f"%{query.keyword}%"),
        ))
    if filters:
        count_q = count_q.where(*filters)
    total = (await db.execute(count_q)).scalar() or 0

    # JOIN 查询
    main_q = (
        select(Score, Course.name.label('course_name'), Course.credit.label('course_credit'),
               Semester.name.label('semester_name'),
               User.real_name.label('student_name'), Student.student_no.label('student_no'))
        .join(Course, Score.course_id == Course.id)
        .join(Semester, Score.semester_id == Semester.id)
        .join(Student, Score.student_id == Student.id)
        .join(User, Student.user_id == User.id)
    )
    if query.college_id or query.major_id:
        main_q = main_q.join(Major, Student.major_id == Major.id)
        if query.college_id:
            main_q = main_q.where(Major.college_id == query.college_id)
        if query.major_id:
            main_q = main_q.where(Student.major_id == query.major_id)
    if query.keyword:
        main_q = main_q.where(or_(
            Student.student_no.like(f"%{query.keyword}%"),
            User.real_name.like(f"%{query.keyword}%"),
        ))
    if filters:
        main_q = main_q.where(*filters)
    main_q = main_q.order_by(Score.id.desc()).limit(query.page_size).offset((query.page - 1) * query.page_size)
    result = await db.execute(main_q)
    rows = result.all()

    return [{
        "id": s.id,
        "student_id": s.student_id,
        "student_name": student_name,
        "student_no": student_no,
        "course_id": s.course_id,
        "course_name": course_name,
        "course_credit": float(course_credit) if course_credit else 0,
        "semester_id": s.semester_id,
        "semester_name": semester_name,
        "score": float(s.score),
        "status": s.status,
        "created_at": str(s.created_at),
        "updated_at": str(s.updated_at),
    } for s, course_name, course_credit, semester_name, student_name, student_no in rows], total


async def list_my_scores(db: AsyncSession, query: ScorePageQuery) -> tuple[list[dict], int]:
    """学生查看自己的成绩（按课程名排序，JOIN课程和学期信息）"""
    from sqlalchemy import select, func, and_
    from app.model.course import Course
    from app.model.semester import Semester

    filters = [Score.student_id == query.student_id]
    if query.semester_id:
        filters.append(Score.semester_id == query.semester_id)
    if query.course_id:
        filters.append(Score.course_id == query.course_id)

    # COUNT
    count_stmt = select(func.count(Score.id)).where(and_(*filters))
    total = (await db.execute(count_stmt)).scalar() or 0

    # 查询并 JOIN
    stmt = (
        select(Score, Course.name.label('course_name'), Course.credit.label('course_credit'),
               Semester.name.label('semester_name'))
        .join(Course, Score.course_id == Course.id)
        .join(Semester, Score.semester_id == Semester.id)
        .where(and_(*filters))
        .order_by(Course.name.asc())
        .limit(query.page_size).offset((query.page - 1) * query.page_size)
    )
    result = await db.execute(stmt)
    rows = result.all()
    items = [{
        "id": s.id,
        "course_name": course_name,
        "course_credit": float(course_credit) if course_credit else 0,
        "semester_name": semester_name,
        "score": float(s.score),
        "status": s.status,
        "created_at": str(s.created_at),
    } for s, course_name, course_credit, semester_name in rows]
    return items, total
