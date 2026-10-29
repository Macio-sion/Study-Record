"""学业预警 Service"""
from datetime import datetime
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.alert_dao import alert_dao
from app.model.alert_record import AlertRecord
from app.model.student import Student
from app.model.user import User
from app.model.major import Major
from app.model.semester import Semester
from app.dto.alert_schema import AlertCreate, AlertHandle, AlertResponse, AlertPageQuery
from app.common.exception import NotFoundException


async def create_alert(db: AsyncSession, req: AlertCreate) -> AlertResponse:
    """创建学业预警"""
    alert = AlertRecord(
        student_id=req.student_id, semester_id=req.semester_id,
        alert_level=req.alert_level, alert_type=req.alert_type,
        description=req.description,
        attendance_rate=req.attendance_rate,
        failed_count=req.failed_count, status='pending',
    )
    alert = await alert_dao.create(db, alert)
    return AlertResponse.model_validate(alert)


async def handle_alert(db: AsyncSession, alert_id: int, handler_id: int, req: AlertHandle) -> AlertResponse:
    """处理预警"""
    alert = await alert_dao.get_by_id(db, alert_id)
    if not alert:
        raise NotFoundException(f"预警记录不存在: id={alert_id}")
    alert = await alert_dao.update(db, alert, **{
        'handler_id': handler_id, 'handle_result': req.handle_result,
        'handled_at': datetime.now(), 'status': 'handled',
    })
    return AlertResponse.model_validate(alert)


async def get_alert(db: AsyncSession, alert_id: int) -> AlertResponse:
    alert = await alert_dao.get_by_id(db, alert_id)
    if not alert:
        raise NotFoundException(f"预警记录不存在: id={alert_id}")
    return AlertResponse.model_validate(alert)


async def list_alerts(db: AsyncSession, query: AlertPageQuery, college_id: int = None) -> tuple[list[dict], int]:
    filters = []
    if query.student_id:
        filters.append(AlertRecord.student_id == query.student_id)
    if query.semester_id:
        filters.append(AlertRecord.semester_id == query.semester_id)
    if query.alert_level:
        filters.append(AlertRecord.alert_level == query.alert_level)
    if query.status:
        filters.append(AlertRecord.status == query.status)
    if hasattr(query, 'keyword') and query.keyword:
        filters.append(or_(
            AlertRecord.description.like(f"%{query.keyword}%"),
            AlertRecord.alert_type.like(f"%{query.keyword}%"),
        ))

    # 学工角色：只看本学院学生的预警
    if college_id:
        college_student_ids = select(Student.id).join(Major, Student.major_id == Major.id).where(Major.college_id == college_id).distinct()
        filters.append(AlertRecord.student_id.in_(college_student_ids))

    # JOIN 查询带名称
    main_q = (
        select(AlertRecord, User.real_name.label('student_name'), Semester.name.label('semester_name'))
        .join(Student, AlertRecord.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .join(Semester, AlertRecord.semester_id == Semester.id)
    )
    count_q = select(func.count()).select_from(AlertRecord)
    count_q = count_q.join(Student, AlertRecord.student_id == Student.id).join(User, Student.user_id == User.id).join(Semester, AlertRecord.semester_id == Semester.id)
    if college_id:
        count_q = count_q.where(AlertRecord.student_id.in_(college_student_ids))

    if filters:
        main_q = main_q.where(*filters)
        count_q = count_q.where(*filters)

    total = (await db.execute(count_q)).scalar() or 0
    main_q = main_q.order_by(AlertRecord.id.desc()).offset((query.page - 1) * query.page_size).limit(query.page_size)
    result = await db.execute(main_q)
    rows = result.all()

    return [{
        "id": a.id, "student_id": a.student_id, "student_name": sn,
        "semester_id": a.semester_id, "semester_name": sname,
        "alert_level": a.alert_level, "alert_type": a.alert_type,
        "description": a.description,
        "attendance_rate": a.attendance_rate, "failed_count": a.failed_count,
        "status": a.status, "handler_id": a.handler_id,
        "handle_result": a.handle_result,
        "handled_at": a.handled_at.isoformat() if a.handled_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    } for a, sn, sname in rows], total
