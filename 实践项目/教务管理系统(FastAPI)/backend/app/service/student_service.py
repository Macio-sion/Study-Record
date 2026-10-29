"""学生与班级管理 Service"""
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.student_dao import student_dao, class_dao
from app.dao.college_dao import major_dao
from app.model.student import Student
from app.model.class_model import Class
from app.model.course_selection import CourseSelection
from app.model.course import Course
from app.model.major import Major
from app.model.user import User
from app.dto.student_schema import StudentCreate, StudentUpdate, StudentResponse, StudentPageQuery
from app.dto.class_schema import ClassCreate, ClassUpdate, ClassResponse, ClassPageQuery
from app.common.exception import NotFoundException


# ========== 班级管理 ==========

async def create_class(db: AsyncSession, req: ClassCreate) -> ClassResponse:
    major = await major_dao.get_by_id(db, req.major_id)
    if not major:
        raise NotFoundException(f"专业不存在: id={req.major_id}")
    cls = Class(class_no=req.class_no, name=req.name, major_id=req.major_id, advisor_id=req.advisor_id, grade=req.grade)
    cls = await class_dao.create(db, cls)
    return ClassResponse.model_validate(cls)

async def update_class(db: AsyncSession, class_id: int, req: ClassUpdate) -> ClassResponse:
    cls = await class_dao.get_by_id(db, class_id)
    if not cls:
        raise NotFoundException(f"班级不存在: id={class_id}")
    cls = await class_dao.update(db, cls, name=req.name, advisor_id=req.advisor_id)
    return ClassResponse.model_validate(cls)

async def delete_class(db: AsyncSession, class_id: int) -> bool:
    if not await class_dao.delete(db, class_id):
        raise NotFoundException(f"班级不存在: id={class_id}")
    return True

async def get_class(db: AsyncSession, class_id: int) -> ClassResponse:
    cls = await class_dao.get_by_id(db, class_id)
    if not cls:
        raise NotFoundException(f"班级不存在: id={class_id}")
    return ClassResponse.model_validate(cls)

async def list_classes(db: AsyncSession, query: ClassPageQuery, teacher_id: int = None, college_id: int = None) -> tuple[list[dict], int]:
    # 基础 JOIN：Class + Major
    main_q = (
        select(
            Class.id, Class.class_no, Class.name, Class.major_id,
            Class.grade, Class.advisor_id, Class.created_at,
            Major.name.label('major_name'),
            func.count(Student.id).label('student_count'),
        )
        .join(Major, Class.major_id == Major.id)
        .outerjoin(Student, Student.class_id == Class.id)
        .group_by(Class.id, Class.class_no, Class.name, Class.major_id,
                   Class.grade, Class.advisor_id, Class.created_at, Major.name)
    )

    # 教师角色：只显示自己课程中有关联学生的班级
    if teacher_id:
        teacher_class_ids = (
            select(Student.class_id)
            .join(CourseSelection, CourseSelection.student_id == Student.id)
            .join(Course, CourseSelection.course_id == Course.id)
            .where(Course.teacher_id == teacher_id)
            .distinct()
        )
        main_q = main_q.where(Class.id.in_(teacher_class_ids))
    # 学院过滤：优先使用查询参数的 college_id，否则使用角色限定的
    effective_college_id = query.college_id or college_id
    if effective_college_id and not teacher_id:
        main_q = main_q.where(Major.college_id == effective_college_id)

    if query.major_id:
        main_q = main_q.where(Class.major_id == query.major_id)
    if query.grade:
        main_q = main_q.where(Class.grade == query.grade)
    if query.keyword:
        main_q = main_q.where(or_(Class.name.like(f"%{query.keyword}%"), Class.class_no.like(f"%{query.keyword}%")))

    # COUNT
    count_q = select(func.count(func.distinct(Class.id)))
    # replicate the same joins and filters for count
    count_q = count_q.select_from(Class).join(Major, Class.major_id == Major.id)
    if teacher_id:
        count_q = count_q.where(Class.id.in_(teacher_class_ids))
    effective_college_id = query.college_id or college_id
    if effective_college_id and not teacher_id:
        count_q = count_q.where(Major.college_id == effective_college_id)
    if query.major_id:
        count_q = count_q.where(Class.major_id == query.major_id)
    if query.grade:
        count_q = count_q.where(Class.grade == query.grade)
    if query.keyword:
        count_q = count_q.where(or_(Class.name.like(f"%{query.keyword}%"), Class.class_no.like(f"%{query.keyword}%")))

    total = (await db.execute(count_q)).scalar() or 0

    main_q = main_q.order_by(Class.class_no).limit(query.page_size).offset((query.page - 1) * query.page_size)
    result = await db.execute(main_q)
    rows = result.all()

    return [{
        "id": cid, "class_no": cno, "name": name, "major_id": mid,
        "grade": grade, "advisor_id": aid, "created_at": str(ca),
        "major_name": mname, "student_count": scount,
    } for cid, cno, name, mid, grade, aid, ca, mname, scount in rows], total


# ========== 学生管理 ==========

async def create_student(db: AsyncSession, req: StudentCreate) -> StudentResponse:
    cls = await class_dao.get_by_id(db, req.class_id)
    if not cls:
        raise NotFoundException(f"班级不存在: id={req.class_id}")
    student = Student(student_no=req.student_no, user_id=req.user_id, major_id=req.major_id, class_id=req.class_id, gender=req.gender, enrollment_year=req.enrollment_year)
    student = await student_dao.create(db, student)
    return StudentResponse.model_validate(student)

async def update_student(db: AsyncSession, student_id: int, req: StudentUpdate) -> StudentResponse:
    student = await student_dao.get_by_id(db, student_id)
    if not student:
        raise NotFoundException(f"学生不存在: id={student_id}")
    student = await student_dao.update(db, student, major_id=req.major_id, class_id=req.class_id, gender=req.gender)
    return StudentResponse.model_validate(student)

async def delete_student(db: AsyncSession, student_id: int) -> bool:
    if not await student_dao.delete(db, student_id):
        raise NotFoundException(f"学生不存在: id={student_id}")
    return True

async def get_student(db: AsyncSession, student_id: int) -> StudentResponse:
    student = await student_dao.get_by_id(db, student_id)
    if not student:
        raise NotFoundException(f"学生不存在: id={student_id}")
    return StudentResponse.model_validate(student)

async def list_students(db: AsyncSession, query: StudentPageQuery, teacher_id: int = None, college_id: int = None) -> tuple[list[dict], int]:
    # JOIN: Student + User + Class + Major
    main_q = (
        select(
            Student.id, Student.student_no, Student.gender,
            Student.enrollment_year, Student.class_id, Student.major_id,
            Student.created_at, Student.updated_at,
            User.real_name.label('name'),
            User.phone.label('phone'),
            Class.name.label('class_name'),
        )
        .join(User, Student.user_id == User.id)
        .join(Class, Student.class_id == Class.id)
    )

    # 教师角色：只看自己课程中的学生
    if teacher_id:
        teacher_student_ids = (
            select(CourseSelection.student_id)
            .join(Course, CourseSelection.course_id == Course.id)
            .where(Course.teacher_id == teacher_id)
            .distinct()
        )
        main_q = main_q.where(Student.id.in_(teacher_student_ids))
    # 学院过滤：优先使用查询参数中的 college_id，否则使用角色自动限定的 college_id
    effective_college_id = query.college_id or college_id
    if effective_college_id and not teacher_id:
        staff_student_ids = (
            select(Student.id)
            .join(Major, Student.major_id == Major.id)
            .where(Major.college_id == effective_college_id)
            .distinct()
        )
        main_q = main_q.where(Student.id.in_(staff_student_ids))

    if query.class_id:
        main_q = main_q.where(Student.class_id == query.class_id)
    if query.major_id:
        main_q = main_q.where(Student.major_id == query.major_id)
    if query.enrollment_year:
        main_q = main_q.where(Student.enrollment_year == query.enrollment_year)
    if query.keyword:
        main_q = main_q.where(or_(
            Student.student_no.like(f"%{query.keyword}%"),
            User.real_name.like(f"%{query.keyword}%"),
        ))

    # COUNT
    count_q = select(func.count(func.distinct(Student.id))).select_from(Student).join(User, Student.user_id == User.id).join(Class, Student.class_id == Class.id)
    if teacher_id:
        count_q = count_q.where(Student.id.in_(teacher_student_ids))
    effective_college_id = query.college_id or college_id
    if effective_college_id and not teacher_id:
        from app.model.major import Major as Mj
        staff_sids = select(Student.id).join(Mj, Student.major_id == Mj.id).where(Mj.college_id == effective_college_id).distinct()
        count_q = count_q.where(Student.id.in_(staff_sids))
    if query.class_id:
        count_q = count_q.where(Student.class_id == query.class_id)
    if query.major_id:
        count_q = count_q.where(Student.major_id == query.major_id)
    if query.enrollment_year:
        count_q = count_q.where(Student.enrollment_year == query.enrollment_year)
    if query.keyword:
        count_q = count_q.where(or_(
            Student.student_no.like(f"%{query.keyword}%"),
            User.real_name.like(f"%{query.keyword}%"),
        ))
    total = (await db.execute(count_q)).scalar() or 0

    main_q = main_q.order_by(Student.student_no).limit(query.page_size).offset((query.page - 1) * query.page_size)
    result = await db.execute(main_q)
    rows = result.all()

    return [{
        "id": sid, "student_no": sno, "gender": g, "enrollment_year": ey,
        "class_id": cid, "major_id": mid, "created_at": str(ca), "updated_at": str(ua),
        "name": name, "phone": phone, "class_name": cname,
    } for sid, sno, g, ey, cid, mid, ca, ua, name, phone, cname in rows], total


async def get_student_by_user_id(db: AsyncSession, user_id: int):
    """根据 user_id 获取学生档案"""
    result = await db.execute(select(Student).where(Student.user_id == user_id))
    return result.scalar_one_or_none()
