"""社团管理 Service"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.club_dao import club_dao, club_member_dao
from app.model.club import Club
from app.model.club_member import ClubMember
from app.model.student import Student
from app.dto.club_schema import ClubCreate, ClubUpdate, ClubResponse, ClubPageQuery, MemberJoin, MemberResponse, MemberApprove
from app.common.exception import NotFoundException, BusinessException


async def _get_student_by_user_id(db: AsyncSession, user_id: int) -> Student:
    result = await db.execute(select(Student).where(Student.user_id == user_id))
    student = result.scalar_one_or_none()
    if not student:
        raise BusinessException(message="当前用户未关联学生档案")
    return student


# ========== 社团 CRUD ==========

async def create_club(db: AsyncSession, req: ClubCreate) -> ClubResponse:
    club = Club(name=req.name, description=req.description, advisor_id=req.advisor_id)
    club = await club_dao.create(db, club)
    return ClubResponse.model_validate(club)


async def update_club(db: AsyncSession, club_id: int, req: ClubUpdate) -> ClubResponse:
    club = await club_dao.get_by_id(db, club_id)
    if not club:
        raise NotFoundException(f"社团不存在: id={club_id}")
    club = await club_dao.update(db, club, name=req.name, description=req.description, advisor_id=req.advisor_id)
    return ClubResponse.model_validate(club)


async def delete_club(db: AsyncSession, club_id: int) -> bool:
    if not await club_dao.delete(db, club_id):
        raise NotFoundException(f"社团不存在: id={club_id}")
    return True


async def get_club(db: AsyncSession, club_id: int) -> ClubResponse:
    club = await club_dao.get_by_id(db, club_id)
    if not club:
        raise NotFoundException(f"社团不存在: id={club_id}")
    return ClubResponse.model_validate(club)


async def list_clubs(db: AsyncSession, query: ClubPageQuery) -> tuple[list[dict], int]:
    from app.model.teacher import Teacher
    from app.model.user import User
    filters = []
    if query.name:
        filters.append(Club.name.like(f"%{query.name}%"))

    # 总数
    count_q = select(func.count()).select_from(Club)
    if filters:
        for f in filters:
            count_q = count_q.where(f)
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # 分页 + JOIN 教师/用户
    main_q = (
        select(Club, User.real_name.label('advisor_name'))
        .join(Teacher, Club.advisor_id == Teacher.id)
        .join(User, Teacher.user_id == User.id)
    )
    if filters:
        for f in filters:
            main_q = main_q.where(f)
    main_q = main_q.order_by(Club.name.asc()).offset((query.page - 1) * query.page_size).limit(query.page_size)
    result = await db.execute(main_q)
    rows = result.all()

    return [{
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "advisor_id": c.advisor_id,
        "advisor_name": advisor_name,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    } for c, advisor_name in rows], total


# ========== 社员管理 ==========

async def join_club(db: AsyncSession, user_id: int, req: MemberJoin) -> MemberResponse:
    """学生加入社团（直接加入，供管理员使用）"""
    student = await _get_student_by_user_id(db, user_id)
    club = await club_dao.get_by_id(db, req.club_id)
    if not club:
        raise NotFoundException(f"社团不存在: id={req.club_id}")
    existing = await club_dao.get_member(db, req.club_id, student.id)
    if existing:
        raise BusinessException(message="你已加入该社团")
    member = ClubMember(club_id=req.club_id, student_id=student.id, role='member', status='approved')
    member = await club_member_dao.create(db, member)
    return MemberResponse.model_validate(member)


async def apply_club(db: AsyncSession, user_id: int, req: MemberJoin) -> MemberResponse:
    """学生申请加入社团（需审批）"""
    student = await _get_student_by_user_id(db, user_id)
    club = await club_dao.get_by_id(db, req.club_id)
    if not club:
        raise NotFoundException(f"社团不存在: id={req.club_id}")
    existing = await club_dao.get_member(db, req.club_id, student.id)
    if existing:
        raise BusinessException(message="你已申请或已加入该社团")
    member = ClubMember(club_id=req.club_id, student_id=student.id, role='member', status='pending')
    member = await club_member_dao.create(db, member)
    return MemberResponse.model_validate(member)


async def approve_member(db: AsyncSession, member_id: int, req: MemberApprove) -> MemberResponse:
    """审批社团申请（教师/学工）"""
    member = await club_member_dao.get_by_id(db, member_id)
    if not member:
        raise NotFoundException(f"成员记录不存在: id={member_id}")
    if member.status != 'pending':
        raise BusinessException(message="当前状态不允许审批")
    if req.approved:
        member = await club_member_dao.update(db, member, status='approved', role=req.role or 'member')
    else:
        member = await club_member_dao.update(db, member, status='rejected')
    return MemberResponse.model_validate(member)


async def list_my_clubs(db: AsyncSession, user_id: int) -> list[dict]:
    """学生查看自己加入的社团"""
    student = await _get_student_by_user_id(db, user_id)
    result = await db.execute(
        select(ClubMember, Club.name)
        .join(Club, ClubMember.club_id == Club.id)
        .where(ClubMember.student_id == student.id)
    )
    rows = result.all()
    return [{
        "id": m.id,
        "club_id": m.club_id,
        "club_name": name,
        "role": m.role,
        "status": m.status,
        "joined_at": m.joined_at,
    } for m, name in rows]


async def leave_club(db: AsyncSession, user_id: int, club_id: int) -> bool:
    """退出社团"""
    student = await _get_student_by_user_id(db, user_id)
    member = await club_dao.get_member(db, club_id, student.id)
    if not member:
        raise BusinessException(message="你未加入该社团")
    return await club_member_dao.delete(db, member.id)


async def remove_member(db: AsyncSession, member_id: int) -> bool:
    """管理员移除社团成员"""
    if not await club_member_dao.delete(db, member_id):
        raise NotFoundException(f"成员记录不存在: id={member_id}")
    return True


async def list_members(db: AsyncSession, club_id: int, page: int = 1, page_size: int = 20) -> tuple[list[MemberResponse], int]:
    items, total = await club_member_dao.get_by_club(db, club_id, page, page_size)
    return [MemberResponse.model_validate(m) for m in items], total
