"""通知公告 Service — 多角色权限矩阵"""
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.notice_dao import notice_dao
from app.model.notice import Notice
from app.model.notice_view import NoticeView
from app.model.notice_recall import NoticeRecallRequest
from app.model.user import User
from app.model.college import College
from app.model.major import Major
from app.model.teacher import Teacher
from app.model.student import Student
from app.model.course import Course
from app.model.course_selection import CourseSelection
from app.model.user_notification import UserNotification
from app.dto.notice_schema import NoticeCreate, NoticeUpdate, NoticeResponse, NoticePageQuery, NoticeRecallCreate, NoticeRecallReview
from app.common.exception import NotFoundException, BusinessException

RECALL_WINDOW_MINUTES = 2


async def _get_teacher(db: AsyncSession, user_id: int) -> Teacher:
    result = await db.execute(select(Teacher).where(Teacher.user_id == user_id))
    t = result.scalar_one_or_none()
    if not t:
        raise BusinessException(message="未找到关联的教师档案")
    return t


async def _get_student(db: AsyncSession, user_id: int) -> Student:
    result = await db.execute(select(Student).where(Student.user_id == user_id))
    s = result.scalar_one_or_none()
    if not s:
        raise BusinessException(message="未找到关联的学生档案")
    return s


async def _get_student_college_id(db: AsyncSession, student_id: int) -> int:
    """获取学生所属学院"""
    result = await db.execute(
        select(Major.college_id).join(Student, Student.major_id == Major.id).where(Student.id == student_id)
    )
    return result.scalar()


async def _can_modify_notice(db: AsyncSession, notice: Notice, user_id: int, role: str) -> bool:
    """检查是否在可修改窗口内或为管理员"""
    if role == 'admin':
        return True
    if notice.publisher_id != user_id:
        return False
    if notice.published_at and datetime.now() - notice.published_at > timedelta(minutes=RECALL_WINDOW_MINUTES):
        return False
    return True


# ==================== CRUD ====================

async def create_notice(db: AsyncSession, user_id: int, role: str, req: NoticeCreate) -> NoticeResponse:
    """创建通知，按角色校验发布权限"""
    # 教师只能向自己课程的学生发布
    if role == 'teacher':
        if req.target_role != 'student':
            raise BusinessException(message="教师只能向学生发布通知")
        req.college_id = None
        req.major_id = None
    # 学工只能向自己学院发布
    elif role == 'academic_staff':
        # 需要获取 staff 的学院信息 — 通过 users 或其他方式。简化：从 teacher 表查（如果没有则需要另外方案）
        # academic_staff 没有 teacher 记录，不能通过 teacher 获取 college。
        # 简化处理：academic_staff 创建通知时必须指定 college_id，不允许为空
        if not req.college_id:
            raise BusinessException(message="学工发布通知必须指定目标学院")
    # 管理员无限制

    notice = Notice(
        title=req.title, content=req.content, publisher_id=user_id,
        target_role=req.target_role, college_id=req.college_id, major_id=req.major_id,
        is_published=False,
    )
    notice = await notice_dao.create(db, notice)
    return await _to_response(db, notice)


async def update_notice(db: AsyncSession, notice_id: int, user_id: int, role: str, req: NoticeUpdate) -> NoticeResponse:
    notice = await notice_dao.get_by_id(db, notice_id)
    if not notice:
        raise NotFoundException(f"通知不存在: id={notice_id}")
    if not await _can_modify_notice(db, notice, user_id, role):
        raise BusinessException(message="发布超过2分钟的通知不可直接修改，请提交撤回申请")
    kwargs = {}
    for field in ['title', 'content', 'target_role', 'college_id', 'major_id', 'is_published']:
        val = getattr(req, field, None)
        if val is not None:
            kwargs[field] = val
    if req.is_published:
        kwargs['published_at'] = datetime.now()
    elif req.is_published is False:
        kwargs['published_at'] = None
    notice = await notice_dao.update(db, notice, **kwargs)
    return await _to_response(db, notice)


async def publish_notice(db: AsyncSession, notice_id: int, user_id: int, role: str) -> NoticeResponse:
    """发布通知，同时给目标用户创建消息通知"""
    notice = await notice_dao.get_by_id(db, notice_id)
    if not notice:
        raise NotFoundException(f"通知不存在: id={notice_id}")
    if notice.publisher_id != user_id and role != 'admin':
        raise BusinessException(message="只能发布自己创建的通知")
    notice = await notice_dao.update(db, notice, is_published=True, published_at=datetime.now())

    # 批量创建 UserNotification 给目标用户
    target_user_ids = await _get_target_user_ids(db, notice)
    for uid in target_user_ids:
        un = UserNotification(
            user_id=uid, title=f"新公告: {notice.title}",
            content=notice.content[:100] if notice.content else '',
            notification_type='notice',
            related_url=f'/notice?id={notice.id}',
        )
        db.add(un)
    await db.flush()
    await db.refresh(notice)
    return await _to_response(db, notice)


async def unpublish_notice(db: AsyncSession, notice_id: int, user_id: int, role: str) -> NoticeResponse:
    """撤回发布"""
    notice = await notice_dao.get_by_id(db, notice_id)
    if not notice:
        raise NotFoundException(f"通知不存在: id={notice_id}")
    if not await _can_modify_notice(db, notice, user_id, role):
        raise BusinessException(message="发布超过2分钟的通知不可直接撤回，请提交撤回申请")
    notice = await notice_dao.update(db, notice, is_published=False, published_at=None)
    return await _to_response(db, notice)


async def delete_notice(db: AsyncSession, notice_id: int, user_id: int, role: str) -> bool:
    notice = await notice_dao.get_by_id(db, notice_id)
    if not notice:
        raise NotFoundException(f"通知不存在: id={notice_id}")
    if role != 'admin' and notice.publisher_id != user_id:
        raise BusinessException(message="只能删除自己创建的通知")
    await notice_dao.delete(db, notice_id)
    return True


async def get_notice(db: AsyncSession, notice_id: int, user_id: int) -> dict:
    """查看通知详情 + 标记已读"""
    notice = await notice_dao.get_by_id(db, notice_id)
    if not notice:
        raise NotFoundException(f"通知不存在: id={notice_id}")

    # 记录查看
    existing = (await db.execute(
        select(NoticeView).where(NoticeView.notice_id == notice_id, NoticeView.user_id == user_id)
    )).scalar_one_or_none()
    if not existing:
        db.add(NoticeView(notice_id=notice_id, user_id=user_id))
        await db.flush()

    return await _to_response(db, notice)


async def list_notices(db: AsyncSession, query: NoticePageQuery, user_id: int, role: str) -> tuple[list[dict], int]:
    """分页列表 — 按角色全权限过滤"""
    filters = _build_base_filters(query)

    # 角色权限过滤
    if role == 'student':
        student = await _get_student(db, user_id)
        role_filters = await _student_notice_filters(db, student)
    elif role == 'teacher':
        teacher = await _get_teacher(db, user_id)
        role_filters = await _teacher_notice_filters(db, teacher)
    elif role == 'academic_staff':
        role_filters = await _staff_notice_filters(db, user_id)
    else:  # admin
        role_filters = []

    filters.extend(role_filters)

    # JOIN 查询
    from app.model.college import College as C
    from app.model.major import Major as M
    main_q = (
        select(Notice, User.real_name.label('publisher_name'),
               C.name.label('college_name'), M.name.label('major_name'))
        .join(User, Notice.publisher_id == User.id)
        .outerjoin(C, Notice.college_id == C.id)
        .outerjoin(M, Notice.major_id == M.id)
    )

    # COUNT
    count_q = select(func.count()).select_from(Notice).join(User, Notice.publisher_id == User.id)
    count_q = count_q.outerjoin(C, Notice.college_id == C.id).outerjoin(M, Notice.major_id == M.id)

    if filters:
        main_q = main_q.where(*filters)
        count_q = count_q.where(*filters)

    total = (await db.execute(count_q)).scalar() or 0
    main_q = main_q.order_by(Notice.id.desc()).offset((query.page - 1) * query.page_size).limit(query.page_size)
    result = await db.execute(main_q)
    rows = result.all()

    return [_row_to_dict(n, pn, cn, mn) for n, pn, cn, mn in rows], total


async def get_unviewed_notices(db: AsyncSession, user_id: int, role: str) -> list[dict]:
    """获取当前用户未查看的已发布公告（用于消息通知）"""
    # 获取用户已查看的 notice_id
    viewed_ids_q = select(NoticeView.notice_id).where(NoticeView.user_id == user_id)
    viewed_ids = (await db.execute(viewed_ids_q)).scalars().all()

    filters = [Notice.is_published == True]
    if viewed_ids:
        filters.append(Notice.id.notin_(viewed_ids))

    # 角色过滤
    if role == 'student':
        student = await _get_student(db, user_id)
        role_filters = await _student_notice_filters(db, student)
    elif role == 'teacher':
        teacher = await _get_teacher(db, user_id)
        role_filters = await _teacher_notice_filters(db, teacher)
    elif role == 'academic_staff':
        role_filters = await _staff_notice_filters(db, user_id)
    else:
        role_filters = []
    filters.extend(role_filters)

    from app.model.college import College as C
    from app.model.major import Major as M
    q = (
        select(Notice, User.real_name.label('publisher_name'),
               C.name.label('college_name'), M.name.label('major_name'))
        .join(User, Notice.publisher_id == User.id)
        .outerjoin(C, Notice.college_id == C.id)
        .outerjoin(M, Notice.major_id == M.id)
        .where(*filters)
        .order_by(Notice.published_at.desc()).limit(20)
    )
    result = await db.execute(q)
    rows = result.all()
    return [_row_to_dict(n, pn, cn, mn) for n, pn, cn, mn in rows]


# ==================== 撤回申请 ====================

async def request_recall(db: AsyncSession, notice_id: int, user_id: int, req: NoticeRecallCreate):
    """提交撤回申请（超时后）"""
    notice = await notice_dao.get_by_id(db, notice_id)
    if not notice:
        raise NotFoundException(f"通知不存在: id={notice_id}")
    if notice.publisher_id != user_id:
        raise BusinessException(message="只能对自己发布的通知提交撤回申请")
    if notice.published_at and datetime.now() - notice.published_at <= timedelta(minutes=RECALL_WINDOW_MINUTES):
        raise BusinessException(message="发布在2分钟内的通知可直接撤回，无需申请")

    existing = (await db.execute(
        select(NoticeRecallRequest).where(
            NoticeRecallRequest.notice_id == notice_id,
            NoticeRecallRequest.status == 'pending'
        )
    )).scalar_one_or_none()
    if existing:
        raise BusinessException(message="该通知已有待审批的撤回申请")

    rr = NoticeRecallRequest(notice_id=notice_id, requester_id=user_id, reason=req.reason)
    db.add(rr)
    await db.flush()
    return {"id": rr.id, "status": rr.status}


async def list_recall_requests(db: AsyncSession, status: str = None) -> list[dict]:
    """管理员查看撤回申请列表"""
    q = select(NoticeRecallRequest, Notice.title.label('notice_title'), User.real_name.label('requester_name')) \
        .join(Notice, NoticeRecallRequest.notice_id == Notice.id) \
        .join(User, NoticeRecallRequest.requester_id == User.id)
    if status:
        q = q.where(NoticeRecallRequest.status == status)
    q = q.order_by(NoticeRecallRequest.created_at.desc())
    result = await db.execute(q)
    rows = result.all()
    return [{
        "id": rr.id, "notice_id": rr.notice_id, "notice_title": nt,
        "requester_id": rr.requester_id, "requester_name": rn,
        "reason": rr.reason, "status": rr.status,
        "created_at": rr.created_at.isoformat() if rr.created_at else None,
    } for rr, nt, rn in rows]


async def review_recall(db: AsyncSession, recall_id: int, reviewer_id: int, req: NoticeRecallReview):
    """审批撤回申请"""
    rr = (await db.execute(
        select(NoticeRecallRequest).where(NoticeRecallRequest.id == recall_id)
    )).scalar_one_or_none()
    if not rr:
        raise NotFoundException(f"撤回申请不存在: id={recall_id}")
    if rr.status != 'pending':
        raise BusinessException(message="该申请已处理")

    rr.status = 'approved' if req.approved else 'rejected'
    rr.reviewer_id = reviewer_id
    rr.review_comment = req.comment
    rr.reviewed_at = datetime.now()

    if req.approved:
        notice = await notice_dao.get_by_id(db, rr.notice_id)
        if notice:
            await notice_dao.update(db, notice, is_published=False, published_at=None)

    await db.flush()
    return {"id": rr.id, "status": rr.status}


# ==================== 内部辅助 ====================

def _build_base_filters(query: NoticePageQuery) -> list:
    filters = []
    if query.is_published is not None:
        filters.append(Notice.is_published == query.is_published)
    if query.target_role:
        filters.append(Notice.target_role == query.target_role)
    if query.college_id:
        filters.append(Notice.college_id == query.college_id)
    if query.major_id:
        filters.append(Notice.major_id == query.major_id)
    if query.keyword:
        filters.append(or_(Notice.title.like(f"%{query.keyword}%"), Notice.content.like(f"%{query.keyword}%")))
    return filters


async def _student_notice_filters(db: AsyncSession, student: Student) -> list:
    """学生可见：all + 发给student且是本人课程的教师/本学院学工/管理员 发布的"""
    from app.model.user import User as U
    # 基础：all 角色
    base = Notice.target_role.in_(['all', 'student'])

    # 教师发布的 → 学生在教师的课程中
    teacher_course_ids = (
        select(CourseSelection.course_id)
        .where(CourseSelection.student_id == student.id)
    )
    teacher_course_ids_list = (await db.execute(teacher_course_ids)).scalars().all()

    teacher_conditions = []
    if teacher_course_ids_list:
        # 获取这些课程的教师
        teacher_ids = (await db.execute(
            select(Course.teacher_id.distinct()).where(Course.id.in_(teacher_course_ids_list))
        )).scalars().all()
        if teacher_ids:
            # 获取教师的 user_id
            teacher_user_ids = (await db.execute(
                select(Teacher.user_id).where(Teacher.id.in_(teacher_ids))
            )).scalars().all()
            if teacher_user_ids:
                teacher_conditions.append(Notice.publisher_id.in_(teacher_user_ids))

    # 学工发布的 → 学生的学院匹配
    student_college_id = await _get_student_college_id(db, student.id)
    staff_condition = and_(Notice.college_id == student_college_id, Notice.publisher_id.in_(
        select(U.id).where(U.role_code == 'academic_staff')
    )) if student_college_id else None

    # 管理员发布的：无额外条件（已包含在 base 中）
    admin_condition = Notice.publisher_id.in_(select(U.id).where(U.role_code == 'admin'))

    # 组合 OR 条件
    sub_conditions = [base]
    if teacher_conditions:
        sub_conditions.append(and_(Notice.target_role == 'student', *teacher_conditions))
    if staff_condition is not None:
        sub_conditions.append(staff_condition)
    sub_conditions.append(admin_condition)

    return [or_(*sub_conditions)]


async def _teacher_notice_filters(db: AsyncSession, teacher: Teacher) -> list:
    """教师可见：自己发布的 + target_role=all/teacher + 学工发布的本学院 + 管理员发布的"""
    from app.model.user import User as U

    conditions = [
        Notice.publisher_id.in_(select(U.id).where(U.id == _get_teacher_user_id(teacher))),
        Notice.target_role.in_(['all', 'teacher']),
    ]

    # 学工发布的本学院公告
    staff_in_college = and_(
        Notice.college_id == teacher.college_id,
        Notice.publisher_id.in_(select(U.id).where(U.role_code == 'academic_staff'))
    )
    conditions.append(staff_in_college)

    # 管理员发布的
    conditions.append(Notice.publisher_id.in_(select(U.id).where(U.role_code == 'admin')))

    return [or_(*conditions)]


def _get_teacher_user_id(teacher: Teacher):
    """返回 teacher 的 user_id，用于子查询"""
    return teacher.user_id


async def _staff_notice_filters(db: AsyncSession, user_id: int) -> list:
    """学工可见：自己发布的 + 本学院所有 + 管理员发布的"""
    from app.model.user import User as U
    # academic_staff 没有 teacher 记录。简化：通过 users 表关联来区分
    # 此处简化为只看所有公告（学工 role 能看到的范围较广）
    conditions = [
        Notice.publisher_id == user_id,
        Notice.publisher_id.in_(select(U.id).where(U.role_code == 'admin')),
    ]
    return [or_(*conditions)]


async def _get_target_user_ids(db: AsyncSession, notice: Notice) -> list[int]:
    """发布时获取所有目标用户ID，用于创建消息通知"""
    from app.model.user import User as U
    target_role = notice.target_role

    if target_role == 'all':
        result = await db.execute(select(U.id))
        return result.scalars().all()

    if notice.college_id:
        # 指定学院
        if target_role == 'teacher':
            result = await db.execute(
                select(Teacher.user_id).where(Teacher.college_id == notice.college_id)
            )
            return result.scalars().all()
        elif target_role == 'student':
            result = await db.execute(
                select(Student.user_id).join(Major, Student.major_id == Major.id)
                .where(Major.college_id == notice.college_id)
            )
            return result.scalars().all()
    else:
        # 不指定学院：教师发布给学生（自己的课程学生）
        if target_role == 'student':
            teacher = (await db.execute(select(Teacher).where(Teacher.user_id == notice.publisher_id))).scalar_one_or_none()
            if teacher:
                result = await db.execute(
                    select(Student.user_id.distinct())
                    .join(CourseSelection, CourseSelection.student_id == Student.id)
                    .join(Course, CourseSelection.course_id == Course.id)
                    .where(Course.teacher_id == teacher.id)
                )
                return result.scalars().all()

        # 全范围
        if target_role == 'teacher':
            result = await db.execute(select(Teacher.user_id))
        else:
            result = await db.execute(select(Student.user_id))
        return result.scalars().all()

    return []


async def _to_response(db: AsyncSession, notice: Notice) -> dict:
    """将 Notice 转为包含关联名称的 dict"""
    from app.model.college import College as C
    from app.model.major import Major as M
    publisher = (await db.execute(select(User).where(User.id == notice.publisher_id))).scalar_one_or_none()
    college = (await db.execute(select(C).where(C.id == notice.college_id))).scalar_one_or_none() if notice.college_id else None
    major = (await db.execute(select(M).where(M.id == notice.major_id))).scalar_one_or_none() if notice.major_id else None

    return {
        "id": notice.id,
        "title": notice.title,
        "content": notice.content,
        "publisher_id": notice.publisher_id,
        "publisher_name": publisher.real_name if publisher else '',
        "target_role": notice.target_role,
        "college_id": notice.college_id,
        "college_name": college.name if college else None,
        "major_id": notice.major_id,
        "major_name": major.name if major else None,
        "is_published": notice.is_published,
        "published_at": notice.published_at.isoformat() if notice.published_at else None,
        "created_at": notice.created_at.isoformat() if notice.created_at else None,
        "updated_at": notice.updated_at.isoformat() if hasattr(notice, 'updated_at') and notice.updated_at else None,
    }


def _row_to_dict(n, pn, cn, mn) -> dict:
    return {
        "id": n.id,
        "title": n.title,
        "content": n.content,
        "publisher_id": n.publisher_id,
        "publisher_name": pn,
        "target_role": n.target_role,
        "college_id": n.college_id,
        "college_name": cn,
        "major_id": n.major_id,
        "major_name": mn,
        "is_published": n.is_published,
        "published_at": n.published_at.isoformat() if n.published_at else None,
        "created_at": n.created_at.isoformat() if n.created_at else None,
        "updated_at": n.updated_at.isoformat() if hasattr(n, 'updated_at') and n.updated_at else None,
    }
