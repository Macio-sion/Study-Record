"""教师管理 Service"""
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.teacher_dao import teacher_dao
from app.dao.college_dao import college_dao
from app.model.teacher import Teacher
from app.model.user import User
from app.model.college import College
from app.dto.teacher_schema import TeacherCreate, TeacherUpdate, TeacherResponse, TeacherPageQuery
from app.common.exception import NotFoundException


async def create_teacher(db: AsyncSession, req: TeacherCreate) -> TeacherResponse:
    college = await college_dao.get_by_id(db, req.college_id)
    if not college:
        raise NotFoundException(f"学院不存在: id={req.college_id}")
    teacher = Teacher(teacher_no=req.teacher_no, user_id=req.user_id, college_id=req.college_id, gender=req.gender, title=req.title)
    teacher = await teacher_dao.create(db, teacher)
    return TeacherResponse.model_validate(teacher)


async def update_teacher(db: AsyncSession, teacher_id: int, req: TeacherUpdate) -> TeacherResponse:
    teacher = await teacher_dao.get_by_id(db, teacher_id)
    if not teacher:
        raise NotFoundException(f"教师不存在: id={teacher_id}")
    if req.college_id:
        college = await college_dao.get_by_id(db, req.college_id)
        if not college:
            raise NotFoundException(f"学院不存在: id={req.college_id}")
    teacher = await teacher_dao.update(db, teacher, college_id=req.college_id, gender=req.gender, title=req.title)
    return TeacherResponse.model_validate(teacher)


async def delete_teacher(db: AsyncSession, teacher_id: int) -> bool:
    if not await teacher_dao.delete(db, teacher_id):
        raise NotFoundException(f"教师不存在: id={teacher_id}")
    return True


async def get_teacher(db: AsyncSession, teacher_id: int) -> TeacherResponse:
    teacher = await teacher_dao.get_by_id(db, teacher_id)
    if not teacher:
        raise NotFoundException(f"教师不存在: id={teacher_id}")
    return TeacherResponse.model_validate(teacher)


async def list_teachers(db: AsyncSession, query: TeacherPageQuery) -> tuple[list[TeacherResponse], int]:
    filters = []
    if query.college_id:
        filters.append(Teacher.college_id == query.college_id)
    if query.keyword:
        filters.append(or_(Teacher.teacher_no.like(f"%{query.keyword}%"), Teacher.title.like(f"%{query.keyword}%")))

    # JOIN 查询
    from sqlalchemy import func
    count_q = select(func.count(Teacher.id))
    if filters:
        count_q = count_q.where(*filters)
    total = (await db.execute(count_q)).scalar() or 0

    main_q = (
        select(Teacher, User.real_name.label('name'), User.phone, User.email, College.name.label('college_name'))
        .join(User, Teacher.user_id == User.id)
        .outerjoin(College, Teacher.college_id == College.id)
        .order_by(Teacher.teacher_no)
        .limit(query.page_size).offset((query.page - 1) * query.page_size)
    )
    if filters:
        main_q = main_q.where(*filters)

    result = await db.execute(main_q)
    rows = result.all()

    return [TeacherResponse(
        id=t.id, teacher_no=t.teacher_no, user_id=t.user_id, college_id=t.college_id,
        gender=t.gender, title=t.title, name=name, phone=phone, email=email,
        college_name=college_name or '', created_at=t.created_at, updated_at=t.updated_at,
    ) for t, name, phone, email, college_name in rows], total


async def get_teacher_by_user_id(db: AsyncSession, user_id: int):
    """根据 user_id 获取教师档案"""
    result = await db.execute(select(Teacher).where(Teacher.user_id == user_id))
    return result.scalar_one_or_none()
