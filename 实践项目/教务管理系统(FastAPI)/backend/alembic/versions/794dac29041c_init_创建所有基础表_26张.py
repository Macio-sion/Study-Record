"""init: 创建所有基础表(26张)

Revision ID: 794dac29041c
Revises: 
Create Date: 2026-07-22 16:19:41.561942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '794dac29041c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建所有26张基础表"""

    # ========== 1. users（用户表） ==========
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(50), nullable=False, comment='用户名'),
        sa.Column('password_hash', sa.String(255), nullable=False, comment='bcrypt密码'),
        sa.Column('role_code', sa.String(20), nullable=False, comment='角色编码'),
        sa.Column('real_name', sa.String(50), nullable=False, comment='真实姓名'),
        sa.Column('phone', sa.String(20), nullable=True, comment='手机号'),
        sa.Column('email', sa.String(100), nullable=True, comment='邮箱'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username', name='uk_username'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index('idx_users_role', 'users', ['role_code'])

    # ========== 2. colleges（学院表） ==========
    op.create_table(
        'colleges',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(10), nullable=False, comment='学院编码'),
        sa.Column('name', sa.String(100), nullable=False, comment='学院名称'),
        sa.Column('description', sa.String(500), nullable=True, comment='学院描述'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uk_college_code'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 3. majors（专业表） ==========
    op.create_table(
        'majors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(10), nullable=False, comment='专业编码'),
        sa.Column('name', sa.String(100), nullable=False, comment='专业名称'),
        sa.Column('college_id', sa.Integer(), nullable=False, comment='所属学院ID'),
        sa.Column('duration', sa.Integer(), nullable=False, server_default='4', comment='学制(年)'),
        sa.Column('degree', sa.String(20), nullable=False, comment='学位类型'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uk_major_code'),
        sa.ForeignKeyConstraint(['college_id'], ['colleges.id'], name='fk_major_college', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 4. classes（班级表） ==========
    op.create_table(
        'classes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('class_no', sa.String(20), nullable=False, comment='班级编号'),
        sa.Column('name', sa.String(100), nullable=False, comment='班级名称'),
        sa.Column('major_id', sa.Integer(), nullable=False, comment='所属专业ID'),
        sa.Column('advisor_id', sa.Integer(), nullable=True, comment='辅导员ID(教师)'),
        sa.Column('grade', sa.Integer(), nullable=False, comment='入学年份'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('class_no', name='uk_class_no'),
        sa.ForeignKeyConstraint(['major_id'], ['majors.id'], name='fk_class_major', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 5. teachers（教师表） ==========
    op.create_table(
        'teachers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('teacher_no', sa.String(20), nullable=False, comment='工号'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='关联用户ID'),
        sa.Column('college_id', sa.Integer(), nullable=False, comment='所属学院ID'),
        sa.Column('gender', sa.String(4), nullable=False, comment='性别'),
        sa.Column('title', sa.String(50), nullable=True, comment='职称'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('teacher_no', name='uk_teacher_no'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_teacher_user', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['college_id'], ['colleges.id'], name='fk_teacher_college', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # 为 classes 的 advisor_id 补充外键（teachers 已创建）
    op.create_foreign_key('fk_class_advisor', 'classes', 'teachers', ['advisor_id'], ['id'], ondelete='SET NULL')

    # ========== 6. students（学生表） ==========
    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_no', sa.String(20), nullable=False, comment='学号'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='关联用户ID'),
        sa.Column('major_id', sa.Integer(), nullable=False, comment='所属专业ID'),
        sa.Column('class_id', sa.Integer(), nullable=False, comment='所属班级ID'),
        sa.Column('gender', sa.String(4), nullable=False, comment='性别'),
        sa.Column('enrollment_year', sa.Integer(), nullable=False, comment='入学年份'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_no', name='uk_student_no'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_student_user', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['major_id'], ['majors.id'], name='fk_student_major', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], name='fk_student_class', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 7. semesters（学期表） ==========
    op.create_table(
        'semesters',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(20), nullable=False, comment='学期名称'),
        sa.Column('start_date', sa.Date(), nullable=False, comment='开始日期'),
        sa.Column('end_date', sa.Date(), nullable=False, comment='结束日期'),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='0', comment='是否当前学期'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 8. courses（课程表） ==========
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(20), nullable=False, comment='课程编码'),
        sa.Column('name', sa.String(200), nullable=False, comment='课程名称'),
        sa.Column('semester_id', sa.Integer(), nullable=False, comment='学期ID'),
        sa.Column('college_id', sa.Integer(), nullable=False, comment='开课学院ID'),
        sa.Column('teacher_id', sa.Integer(), nullable=False, comment='授课教师ID'),
        sa.Column('credit', sa.DECIMAL(3, 1), nullable=False, comment='学分'),
        sa.Column('max_capacity', sa.Integer(), nullable=False, comment='最大容量'),
        sa.Column('selected_count', sa.Integer(), nullable=False, server_default='0', comment='已选人数'),
        sa.Column('hours', sa.Integer(), nullable=False, comment='总学时'),
        sa.Column('type', sa.String(20), nullable=False, comment='必修/选修'),
        sa.Column('description', sa.String(500), nullable=True, comment='课程描述'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1', comment='乐观锁版本号'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], name='fk_course_semester', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['college_id'], ['colleges.id'], name='fk_course_college', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], name='fk_course_teacher', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index('idx_course_semester', 'courses', ['semester_id'])
    op.create_index('idx_course_teacher', 'courses', ['teacher_id'])

    # ========== 9. classrooms（教室表） ==========
    op.create_table(
        'classrooms',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('room_no', sa.String(20), nullable=False, comment='教室编号'),
        sa.Column('name', sa.String(100), nullable=False, comment='教室名称'),
        sa.Column('building', sa.String(50), nullable=False, comment='教学楼'),
        sa.Column('capacity', sa.Integer(), nullable=False, comment='容量'),
        sa.Column('type', sa.String(20), nullable=False, comment='教室类型'),
        sa.Column('status', sa.String(10), nullable=False, server_default='available', comment='状态'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_no', name='uk_room_no'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 10. schedules（排课结果表） ==========
    op.create_table(
        'schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('classroom_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('semester_id', sa.Integer(), nullable=False),
        sa.Column('week_start', sa.Integer(), nullable=False, comment='起始周次'),
        sa.Column('week_end', sa.Integer(), nullable=False, comment='结束周次'),
        sa.Column('day_of_week', sa.Integer(), nullable=False, comment='星期(1-7)'),
        sa.Column('period_start', sa.Integer(), nullable=False, comment='起始节次'),
        sa.Column('period_end', sa.Integer(), nullable=False, comment='结束节次'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('classroom_id', 'semester_id', 'week_start', 'day_of_week', 'period_start', name='uk_slot'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name='fk_schedule_course', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], name='fk_schedule_classroom', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], name='fk_schedule_teacher', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], name='fk_schedule_semester', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index('idx_schedule_teacher_week', 'schedules', ['teacher_id', 'semester_id', 'week_start'])
    op.create_index('idx_schedule_course', 'schedules', ['course_id'])

    # ========== 11. course_selections（选课记录表） ==========
    op.create_table(
        'course_selections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('semester_id', sa.Integer(), nullable=False),
        sa.Column('selected_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('status', sa.String(10), nullable=False, server_default='selected', comment='selected/dropped'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'course_id', 'semester_id', name='uk_student_course'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='fk_selection_student', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name='fk_selection_course', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], name='fk_selection_semester', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index('idx_selection_student', 'course_selections', ['student_id', 'semester_id'])

    # ========== 12. attendances（出勤记录表） ==========
    op.create_table(
        'attendances',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False, comment='点名教师ID'),
        sa.Column('date', sa.Date(), nullable=False, comment='上课日期'),
        sa.Column('status', sa.String(20), nullable=False, comment='present/late/early_leave/absent'),
        sa.Column('remark', sa.String(200), nullable=True, comment='备注'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'student_id', 'date', name='uk_course_student_date'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name='fk_attendance_course', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='fk_attendance_student', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], name='fk_attendance_teacher', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index('idx_attendance_student', 'attendances', ['student_id'])

    # ========== 13. scores（成绩表） ==========
    op.create_table(
        'scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('semester_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.DECIMAL(5, 1), nullable=False, comment='成绩(0-100)'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft', comment='draft/published/locked'),
        sa.Column('teacher_id', sa.Integer(), nullable=False, comment='录入教师ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'course_id', 'semester_id', name='uk_student_course_semester'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='fk_score_student', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name='fk_score_course', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], name='fk_score_semester', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], name='fk_score_teacher', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 14. score_logs（成绩修改日志表） ==========
    op.create_table(
        'score_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('score_id', sa.Integer(), nullable=False),
        sa.Column('old_score', sa.DECIMAL(5, 1), nullable=True, comment='原值'),
        sa.Column('new_score', sa.DECIMAL(5, 1), nullable=True, comment='新值'),
        sa.Column('operator_id', sa.Integer(), nullable=False, comment='操作人ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['score_id'], ['scores.id'], name='fk_score_log_score', ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 15. assignments（作业表） ==========
    op.create_table(
        'assignments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False, comment='作业标题'),
        sa.Column('content', sa.Text(), nullable=True, comment='作业内容'),
        sa.Column('file_path', sa.String(500), nullable=True, comment='附件路径'),
        sa.Column('deadline', sa.DateTime(), nullable=False, comment='截止时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name='fk_assignment_course', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], name='fk_assignment_teacher', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 16. assignment_submissions（作业提交表） ==========
    op.create_table(
        'assignment_submissions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True, comment='提交内容'),
        sa.Column('file_path', sa.String(500), nullable=True, comment='提交附件'),
        sa.Column('score', sa.DECIMAL(5, 1), nullable=True, comment='评分'),
        sa.Column('comment', sa.String(500), nullable=True, comment='评语'),
        sa.Column('submitted_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True, comment='批阅时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assignment_id', 'student_id', name='uk_assignment_student'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], name='fk_submission_assignment', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='fk_submission_student', ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 17. leave_requests（请假申请表） ==========
    op.create_table(
        'leave_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('leave_type', sa.String(20), nullable=False, comment='事假/病假/公假'),
        sa.Column('leave_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending_teacher', comment='审批状态'),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.Column('teacher_opinion', sa.String(200), nullable=True),
        sa.Column('teacher_at', sa.DateTime(), nullable=True),
        sa.Column('staff_id', sa.Integer(), nullable=True),
        sa.Column('staff_opinion', sa.String(200), nullable=True),
        sa.Column('staff_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='fk_leave_student', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name='fk_leave_course', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], name='fk_leave_teacher', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['staff_id'], ['users.id'], name='fk_leave_staff', ondelete='SET NULL'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 18. alert_records（预警记录表） ==========
    op.create_table(
        'alert_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('semester_id', sa.Integer(), nullable=False),
        sa.Column('alert_level', sa.String(20), nullable=False, comment='yellow/orange/red'),
        sa.Column('attendance_rate', sa.DECIMAL(5, 2), nullable=True, comment='出勤率'),
        sa.Column('failed_count', sa.Integer(), nullable=True, comment='不及格门数'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', comment='pending/processing/resolved'),
        sa.Column('handler_id', sa.Integer(), nullable=True, comment='处理人ID'),
        sa.Column('handle_result', sa.String(500), nullable=True),
        sa.Column('handled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='fk_alert_student', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], name='fk_alert_semester', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 19. clubs（社团表） ==========
    op.create_table(
        'clubs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False, comment='社团名称'),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('advisor_id', sa.Integer(), nullable=False, comment='指导老师ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uk_club_name'),
        sa.ForeignKeyConstraint(['advisor_id'], ['teachers.id'], name='fk_club_advisor', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 20. club_members（社团成员表） ==========
    op.create_table(
        'club_members',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('club_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='member', comment='leader/manager/member'),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('club_id', 'student_id', name='uk_club_student'),
        sa.ForeignKeyConstraint(['club_id'], ['clubs.id'], name='fk_club_member_club', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], name='fk_club_member_student', ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 21. notices（通知公告表） ==========
    op.create_table(
        'notices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(200), nullable=False, comment='公告标题'),
        sa.Column('content', sa.Text(), nullable=True, comment='公告内容'),
        sa.Column('publisher_id', sa.Integer(), nullable=False, comment='发布人ID'),
        sa.Column('visible_to', sa.String(20), nullable=False, server_default='all', comment='可见范围:all/teacher/student'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['publisher_id'], ['users.id'], name='fk_notice_publisher', ondelete='RESTRICT'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 22. roles（角色定义表） ==========
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(20), nullable=False, comment='角色编码'),
        sa.Column('name', sa.String(50), nullable=False, comment='角色名称'),
        sa.Column('description', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uk_role_code'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 23. permissions（权限表） ==========
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(50), nullable=False, comment='权限编码'),
        sa.Column('name', sa.String(100), nullable=False, comment='权限名称'),
        sa.Column('module', sa.String(50), nullable=False, comment='所属模块'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uk_permission_code'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 24. role_permissions（角色-权限关联表） ==========
    op.create_table(
        'role_permissions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uk_role_permission'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name='fk_rp_role', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], name='fk_rp_permission', ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )

    # ========== 25. user_logs（操作日志表） ==========
    op.create_table(
        'user_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(100), nullable=False, comment='操作类型'),
        sa.Column('module', sa.String(50), nullable=False, comment='操作模块'),
        sa.Column('target_id', sa.Integer(), nullable=True, comment='操作对象ID'),
        sa.Column('detail', sa.Text(), nullable=True, comment='操作详情JSON'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_log_user', ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index('idx_user_logs_time', 'user_logs', ['created_at'])
    op.create_index('idx_user_logs_user', 'user_logs', ['user_id'])

    # ========== 26. import_records（批量导入记录表） ==========
    op.create_table(
        'import_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('type', sa.String(20), nullable=False, comment='导入类型:teacher/student'),
        sa.Column('total_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fail_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fail_detail', sa.Text(), nullable=True, comment='失败详情JSON'),
        sa.Column('file_name', sa.String(200), nullable=False),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='processing', comment='processing/completed/failed'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id'], name='fk_import_operator', ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )


def downgrade() -> None:
    """删除所有表（逆序）"""
    op.drop_table('import_records')
    op.drop_table('user_logs')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('notices')
    op.drop_table('club_members')
    op.drop_table('clubs')
    op.drop_table('alert_records')
    op.drop_table('leave_requests')
    op.drop_table('assignment_submissions')
    op.drop_table('assignments')
    op.drop_table('score_logs')
    op.drop_table('scores')
    op.drop_table('attendances')
    op.drop_table('course_selections')
    op.drop_table('schedules')
    op.drop_table('classrooms')
    op.drop_table('courses')
    op.drop_table('semesters')
    op.drop_table('students')
    op.drop_table('classes')
    op.drop_table('teachers')
    op.drop_table('majors')
    op.drop_table('colleges')
    op.drop_table('users')
