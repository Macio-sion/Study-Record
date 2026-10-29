"""
仪表盘统计接口
提供聚合统计数据，按角色返回不同数据
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.database import get_db
from app.common.response import success
from app.common.permission import get_current_user
from app.model.student import Student
from app.model.teacher import Teacher
from app.model.course import Course
from app.model.attendance import Attendance
from app.model.college import College
from app.model.major import Major
from app.model.user_log import UserLog
from app.model.user import User
from app.model.notice import Notice
from app.model.score import Score
from app.model.assignment import Assignment
from app.model.assignment_submission import AssignmentSubmission
from app.model.leave_request import LeaveRequest
from app.model.alert_record import AlertRecord
from app.model.course_selection import CourseSelection
from app.model.club import Club

router = APIRouter(prefix="/api", tags=["仪表盘"])


@router.get("/dashboard/stats", summary="仪表盘统计数据（按角色）")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    role = current_user.role_code
    user_id = current_user.id

    # 先解析教师/学生档案
    teacher = None
    student = None
    if role == "teacher":
        teacher = await _get_teacher(db, user_id)
    elif role == "student":
        student = await _get_student(db, user_id)

    data = await _get_common_data(db, role, user_id, teacher, student)

    if role == "admin":
        data.update(await _get_admin_data(db))
    elif role == "teacher":
        if teacher:
            data.update(await _get_teacher_data(db, teacher))
    elif role == "student":
        if student:
            data.update(await _get_student_data(db, student))
    elif role == "academic_staff":
        data.update(await _get_staff_data(db, current_user))

    return success(data=data)


# ========== Helpers ==========

async def _get_teacher(db, user_id):
    result = await db.execute(select(Teacher).where(Teacher.user_id == user_id))
    return result.scalar_one_or_none()


async def _get_student(db, user_id):
    result = await db.execute(select(Student).where(Student.user_id == user_id))
    return result.scalar_one_or_none()


async def _get_common_data(db, role, user_id, teacher=None, student=None):
    """所有角色通用的基础数据（公告按角色过滤）"""
    # 最近公告 — 按角色过滤
    notice_query = select(Notice).where(Notice.is_published == True)
    if role == 'student':
        notice_query = notice_query.where(Notice.target_role.in_(['all', 'student']))
    elif role == 'teacher':
        # 教师只看 all/teacher 的公告 + 自己发布的
        notice_query = notice_query.where(or_(
            Notice.target_role.in_(['all', 'teacher']),
            Notice.publisher_id == user_id,
        ))
    elif role == 'academic_staff':
        notice_query = notice_query.where(Notice.target_role.in_(['all', 'teacher', 'student']))
    recent_notices = (await db.execute(
        notice_query.order_by(Notice.published_at.desc()).limit(5)
    )).scalars().all()
    notices_data = [{"id": n.id, "title": n.title,
                     "published_at": n.published_at.isoformat() if n.published_at else ""}
                    for n in recent_notices]

    # 最近操作日志
    recent_logs = (await db.execute(
        select(UserLog).order_by(UserLog.created_at.desc()).limit(5)
    )).scalars().all()
    logs_data = []
    for log in recent_logs:
        user = (await db.execute(select(User).where(User.id == log.user_id))).scalar_one_or_none()
        logs_data.append({
            "id": log.id, "action": log.action, "module": log.module,
            "username": user.username if user else "",
            "created_at": log.created_at.isoformat() if log.created_at else "",
        })

    return {"recent_notices": notices_data, "recent_logs": logs_data}


async def _get_admin_data(db):
    """管理员全局统计"""
    student_count = (await db.execute(select(func.count()).select_from(Student))).scalar() or 0
    teacher_count = (await db.execute(select(func.count()).select_from(Teacher))).scalar() or 0
    course_count = (await db.execute(select(func.count()).select_from(Course))).scalar() or 0
    total_att = (await db.execute(select(func.count()).select_from(Attendance))).scalar() or 0
    present = (await db.execute(
        select(func.count()).select_from(Attendance).where(Attendance.status == "出勤")
    )).scalar() or 0
    attendance_rate = round(present / total_att * 100, 1) if total_att > 0 else 0

    # 学院分布
    colleges = (await db.execute(select(College))).scalars().all()
    college_distribution = []
    for c in colleges:
        cnt = (await db.execute(
            select(func.count()).select_from(Student).join(Major, Student.major_id == Major.id)
            .where(Major.college_id == c.id)
        )).scalar() or 0
        if cnt > 0:
            college_distribution.append({"name": c.name, "value": cnt})

    # 待处理预警数
    pending_alerts = (await db.execute(
        select(func.count()).select_from(AlertRecord).where(AlertRecord.status == "pending")
    )).scalar() or 0
    # 待审批请假数
    pending_leaves = (await db.execute(
        select(func.count()).select_from(LeaveRequest).where(
            LeaveRequest.status.in_(['pending_teacher', 'pending_staff'])
        )
    )).scalar() or 0

    return {
        "role": "admin",
        "kpi": [
            {"label": "在校学生", "value": student_count, "icon": "UserFilled", "color": "#409EFF"},
            {"label": "在职教师", "value": teacher_count, "icon": "Avatar", "color": "#67C23A"},
            {"label": "开设课程", "value": course_count, "icon": "Reading", "color": "#E6A23C"},
            {"label": "出勤率", "value": f"{attendance_rate}%", "icon": "DataAnalysis", "color": "#F56C6C"},
        ],
        "charts": {
            "college_distribution": college_distribution,
            "pending_alerts": pending_alerts,
            "pending_leaves": pending_leaves,
        },
    }


async def _get_teacher_data(db, teacher):
    """教师专属统计"""
    # 授课数量
    course_count = (await db.execute(
        select(func.count()).select_from(Course).where(Course.teacher_id == teacher.id)
    )).scalar() or 0

    # 授课学生数（选了这些课的学生去重）
    my_course_ids = (await db.execute(
        select(Course.id).where(Course.teacher_id == teacher.id)
    )).scalars().all()
    student_count = 0
    if my_course_ids:
        student_count = (await db.execute(
            select(func.count(func.distinct(CourseSelection.student_id)))
            .where(CourseSelection.course_id.in_(my_course_ids))
        )).scalar() or 0

    # 作业批改进度（已批 / 总提交）
    my_assignments = (await db.execute(
        select(Assignment.id).where(Assignment.teacher_id == teacher.id)
    )).scalars().all()
    total_sub = 0
    reviewed_sub = 0
    if my_assignments:
        total_sub = (await db.execute(
            select(func.count()).select_from(AssignmentSubmission)
            .where(AssignmentSubmission.assignment_id.in_(my_assignments))
        )).scalar() or 0
        reviewed_sub = (await db.execute(
            select(func.count()).select_from(AssignmentSubmission)
            .where(AssignmentSubmission.assignment_id.in_(my_assignments),
                   AssignmentSubmission.score.isnot(None))
        )).scalar() or 0

    # 学生出勤率
    total_att = (await db.execute(
        select(func.count()).select_from(Attendance).where(Attendance.teacher_id == teacher.id)
    )).scalar() or 0
    present = (await db.execute(
        select(func.count()).select_from(Attendance)
        .where(Attendance.teacher_id == teacher.id, Attendance.status == "出勤")
    )).scalar() or 0
    attendance_rate = round(present / total_att * 100, 1) if total_att > 0 else 0

    # 待审批请假（仅限本人授课课程中等待教师审批的）
    pending_leaves = 0
    if my_course_ids:
        pending_leaves = (await db.execute(
            select(func.count()).select_from(LeaveRequest)
            .where(LeaveRequest.status == 'pending_teacher',
                   LeaveRequest.course_id.in_(my_course_ids))
        )).scalar() or 0

    # 本周课程（简化：返回课程列表）
    my_courses = (await db.execute(
        select(Course).where(Course.teacher_id == teacher.id).limit(5)
    )).scalars().all()
    week_courses = [{"id": c.id, "name": c.name} for c in my_courses]

    return {
        "role": "teacher",
        "kpi": [
            {"label": "授课课程", "value": course_count, "icon": "Reading", "color": "#409EFF"},
            {"label": "授课学生", "value": student_count, "icon": "UserFilled", "color": "#67C23A"},
            {"label": "学生出勤率", "value": f"{attendance_rate}%", "icon": "DataAnalysis", "color": "#E6A23C"},
            {"label": "作业批改", "value": f"{reviewed_sub}/{total_sub}", "icon": "Document", "color": "#F56C6C"},
        ],
        "charts": {
            "pending_leaves": pending_leaves,
            "week_courses": week_courses,
            "assignment_rate": round(reviewed_sub / total_sub * 100, 1) if total_sub > 0 else 0,
        },
    }


async def _get_student_data(db, student):
    """学生专属统计"""
    # 已选课程数
    course_count = (await db.execute(
        select(func.count()).select_from(CourseSelection)
        .where(CourseSelection.student_id == student.id)
    )).scalar() or 0

    # 出勤率
    total_att = (await db.execute(
        select(func.count()).select_from(Attendance).where(Attendance.student_id == student.id)
    )).scalar() or 0
    present = (await db.execute(
        select(func.count()).select_from(Attendance)
        .where(Attendance.student_id == student.id, Attendance.status == "出勤")
    )).scalar() or 0
    attendance_rate = round(present / total_att * 100, 1) if total_att > 0 else 0

    # 作业提交率
    my_course_ids = (await db.execute(
        select(CourseSelection.course_id).where(CourseSelection.student_id == student.id)
    )).scalars().all()
    assignments_for_me = []
    if my_course_ids:
        assignments_for_me = (await db.execute(
            select(Assignment.id).where(Assignment.course_id.in_(my_course_ids))
        )).scalars().all()
    total_ass = len(assignments_for_me)
    submitted = 0
    if assignments_for_me:
        submitted = (await db.execute(
            select(func.count()).select_from(AssignmentSubmission)
            .where(AssignmentSubmission.student_id == student.id,
                   AssignmentSubmission.assignment_id.in_(assignments_for_me))
        )).scalar() or 0
    assignment_rate = round(submitted / total_ass * 100, 1) if total_ass > 0 else 0

    # 平均成绩
    avg_score = (await db.execute(
        select(func.avg(Score.score)).where(Score.student_id == student.id)
    )).scalar()
    avg_score = round(float(avg_score), 1) if avg_score else 0

    # GPA趋势（最近成绩列表）
    scores = (await db.execute(
        select(Score.score, Score.status).where(Score.student_id == student.id)
        .order_by(Score.created_at.desc()).limit(6)
    )).all()
    score_trend = [{"value": float(s[0]), "status": s[1]} for s in scores]

    # 本周课表
    from app.model.schedule import Schedule
    if my_course_ids:
        schedules = (await db.execute(
            select(Schedule).where(Schedule.course_id.in_(my_course_ids))
            .order_by(Schedule.day_of_week, Schedule.period_start).limit(5)
        )).scalars().all()
    else:
        schedules = []
    week_schedule = []
    for s in schedules:
        course = (await db.execute(select(Course).where(Course.id == s.course_id))).scalar_one_or_none()
        week_schedule.append({
            "day": s.day_of_week, "period_start": s.period_start,
            "course_name": course.name if course else "",
        })

    return {
        "role": "student",
        "kpi": [
            {"label": "已选课程", "value": course_count, "icon": "Reading", "color": "#409EFF"},
            {"label": "出勤率", "value": f"{attendance_rate}%", "icon": "Checked", "color": "#67C23A"},
            {"label": "作业提交率", "value": f"{assignment_rate}%", "icon": "Document", "color": "#E6A23C"},
            {"label": "平均成绩", "value": avg_score, "icon": "Trophy", "color": "#F56C6C"},
        ],
        "charts": {
            "score_trend": score_trend,
            "week_schedule": week_schedule,
        },
    }


async def _get_staff_data(db, current_user):
    """学工处专属统计"""
    college_id = current_user.managed_college_id
    student_count = (await db.execute(select(func.count()).select_from(Student))).scalar() or 0

    # 预警数：按管辖学院过滤
    if college_id:
        staff_student_ids = select(Student.id).join(Major, Student.major_id == Major.id).where(Major.college_id == college_id).distinct()
        pending_alerts = (await db.execute(
            select(func.count()).select_from(AlertRecord)
            .where(AlertRecord.status == "pending", AlertRecord.student_id.in_(staff_student_ids))
        )).scalar() or 0
    else:
        pending_alerts = (await db.execute(
            select(func.count()).select_from(AlertRecord).where(AlertRecord.status == "pending")
        )).scalar() or 0

    # 待审批请假：按管辖学院过滤
    if college_id:
        pending_leaves = (await db.execute(
            select(func.count()).select_from(LeaveRequest)
            .join(Student, LeaveRequest.student_id == Student.id)
            .join(Major, Student.major_id == Major.id)
            .where(Major.college_id == college_id,
                   LeaveRequest.status.in_(['pending_teacher', 'pending_staff']))
        )).scalar() or 0
    else:
        pending_leaves = (await db.execute(
            select(func.count()).select_from(LeaveRequest).where(
                LeaveRequest.status.in_(['pending_teacher', 'pending_staff'])
            )
        )).scalar() or 0
    club_count = (await db.execute(select(func.count()).select_from(Club))).scalar() or 0
    attendance_rate = 0
    total_att = (await db.execute(select(func.count()).select_from(Attendance))).scalar() or 0
    present = (await db.execute(
        select(func.count()).select_from(Attendance).where(Attendance.status == "出勤")
    )).scalar() or 0
    if total_att > 0:
        attendance_rate = round(present / total_att * 100, 1)

    # 学院分布
    colleges = (await db.execute(select(College))).scalars().all()
    college_distribution = []
    for c in colleges:
        cnt = (await db.execute(
            select(func.count()).select_from(Student).join(Major, Student.major_id == Major.id)
            .where(Major.college_id == c.id)
        )).scalar() or 0
        if cnt > 0:
            college_distribution.append({"name": c.name, "value": cnt})

    return {
        "role": "academic_staff",
        "kpi": [
            {"label": "在校学生", "value": student_count, "icon": "UserFilled", "color": "#409EFF"},
            {"label": "待处理预警", "value": pending_alerts, "icon": "WarningFilled", "color": "#E6A23C"},
            {"label": "待审批请假", "value": pending_leaves, "icon": "Clock", "color": "#F56C6C"},
            {"label": "社团数量", "value": club_count, "icon": "StarFilled", "color": "#67C23A"},
        ],
        "charts": {
            "college_distribution": college_distribution,
            "attendance_rate": attendance_rate,
            "pending_alerts": pending_alerts,
            "pending_leaves": pending_leaves,
        },
    }
