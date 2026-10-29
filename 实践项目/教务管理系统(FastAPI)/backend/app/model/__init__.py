"""
模型包 - 导入所有模型以便 Alembic 自动生成迁移
"""
from app.model.base import Base
from app.model.role import Role
from app.model.permission import Permission
from app.model.role_permission import RolePermission
from app.model.user import User
from app.model.college import College
from app.model.major import Major
from app.model.class_model import Class
from app.model.teacher import Teacher
from app.model.student import Student
from app.model.semester import Semester
from app.model.course import Course
from app.model.classroom import Classroom
from app.model.schedule import Schedule
from app.model.course_selection import CourseSelection
from app.model.attendance import Attendance
from app.model.score import Score
from app.model.score_log import ScoreLog
from app.model.assignment import Assignment
from app.model.assignment_submission import AssignmentSubmission
from app.model.leave_request import LeaveRequest
from app.model.alert_record import AlertRecord
from app.model.club import Club
from app.model.club_member import ClubMember
from app.model.notice import Notice
from app.model.notice_view import NoticeView
from app.model.notice_recall import NoticeRecallRequest
from app.model.user_log import UserLog
from app.model.import_record import ImportRecord

__all__ = [
    "Base",
    "User", "Role", "Permission", "RolePermission",
    "College", "Major", "Class", "Teacher", "Student",
    "Semester", "Course", "Classroom", "Schedule", "CourseSelection",
    "Attendance", "Score", "ScoreLog",
    "Assignment", "AssignmentSubmission",
    "LeaveRequest", "AlertRecord",
    "Club", "ClubMember",
    "Notice", "NoticeView", "NoticeRecallRequest",
    "UserLog", "ImportRecord",
]
