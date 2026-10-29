"""种子数据脚本：为所有表插入完整测试数据"""
import asyncio
import sys
import random
sys.path.insert(0, '.')
from app.database import AsyncSessionLocal
from sqlalchemy import text
from app.common.security import hash_password


async def seed():
    async with AsyncSessionLocal() as db:
        # ===== 清理旧数据 =====
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        tables = [
            "assignment_submissions", "assignments", "score_logs", "scores", "attendances",
            "course_selections", "schedules", "notices",
            "club_members", "clubs", "alert_records", "leave_requests",
            "user_notifications", "import_records", "user_logs",
            "role_permissions", "permissions", "roles",
            "students", "teachers", "classes", "courses",
            "majors", "semesters", "classrooms", "colleges",
            "users",
        ]
        for t in tables:
            await db.execute(text(f"TRUNCATE TABLE {t}"))
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

        # ==========================================
        # 1. RBAC 角色与权限
        # ==========================================
        from app.model.role import Role
        from app.model.permission import Permission
        from app.model.role_permission import RolePermission

        roles_data = [
            Role(code="admin", name="管理员", description="系统最高权限"),
            Role(code="teacher", name="教师", description="授课教师权限"),
            Role(code="academic_staff", name="教务人员", description="学工/教务管理权限"),
            Role(code="student", name="学生", description="学生权限"),
        ]
        db.add_all(roles_data)
        await db.flush()
        role_admin, role_teacher, role_staff, role_student = roles_data

        perms = [
            Permission(code="user:list", name="查看用户列表", module="用户管理"),
            Permission(code="user:create", name="创建用户", module="用户管理"),
            Permission(code="user:edit", name="编辑用户", module="用户管理"),
            Permission(code="user:delete", name="删除用户", module="用户管理"),
            Permission(code="student:list", name="查看学生列表", module="学生管理"),
            Permission(code="student:create", name="创建学生", module="学生管理"),
            Permission(code="student:edit", name="编辑学生", module="学生管理"),
            Permission(code="student:delete", name="删除学生", module="学生管理"),
            Permission(code="course:list", name="查看课程列表", module="课程管理"),
            Permission(code="course:create", name="创建课程", module="课程管理"),
            Permission(code="course:edit", name="编辑课程", module="课程管理"),
            Permission(code="course:delete", name="删除课程", module="课程管理"),
            Permission(code="score:list", name="查看成绩", module="成绩管理"),
            Permission(code="score:create", name="录入成绩", module="成绩管理"),
            Permission(code="score:edit", name="修改成绩", module="成绩管理"),
            Permission(code="schedule:list", name="查看排课", module="排课管理"),
            Permission(code="schedule:create", name="创建排课", module="排课管理"),
            Permission(code="schedule:edit", name="编辑排课", module="排课管理"),
            Permission(code="attendance:list", name="查看考勤", module="考勤管理"),
            Permission(code="attendance:edit", name="修改考勤", module="考勤管理"),
            Permission(code="notice:manage", name="管理通知", module="通知管理"),
            Permission(code="alert:manage", name="管理预警", module="预警管理"),
            Permission(code="leave:approve", name="审批请假", module="请假管理"),
            Permission(code="log:view", name="查看日志", module="系统日志"),
        ]
        db.add_all(perms)
        await db.flush()

        # 管理员拥有全部权限
        db.add_all([RolePermission(role_id=role_admin.id, permission_id=p.id) for p in perms])
        # 教务人员拥有大部分管理权限
        staff_perms = ["user:list", "student:list", "student:create", "student:edit",
                       "course:list", "course:create", "course:edit",
                       "score:list", "schedule:list", "schedule:create", "schedule:edit",
                       "attendance:list", "notice:manage", "alert:manage", "leave:approve", "log:view"]
        for sp in staff_perms:
            p = next((x for x in perms if x.code == sp), None)
            if p:
                db.add(RolePermission(role_id=role_staff.id, permission_id=p.id))
        # 教师权限
        teacher_perms = ["course:list", "score:list", "score:create", "score:edit",
                         "schedule:list", "attendance:list", "attendance:edit",
                         "student:list"]
        for tp in teacher_perms:
            p = next((x for x in perms if x.code == tp), None)
            if p:
                db.add(RolePermission(role_id=role_teacher.id, permission_id=p.id))
        # 学生权限
        student_perms = ["course:list", "score:list", "schedule:list", "attendance:list"]
        for sp in student_perms:
            p = next((x for x in perms if x.code == sp), None)
            if p:
                db.add(RolePermission(role_id=role_student.id, permission_id=p.id))

        # ==========================================
        # 2. 用户
        # ==========================================
        from app.model.user import User
        users = [
            User(username="admin", password_hash=hash_password("admin123"), real_name="系统管理员", role_code="admin", is_active=True, phone="13800000001", email="admin@edu.cn"),
            # 教务人员
            User(username="staff1", password_hash=hash_password("123456"), real_name="李学工", role_code="academic_staff", is_active=True, phone="13800002222", email="staff1@edu.cn", managed_college_id=1),
            User(username="staff2", password_hash=hash_password("123456"), real_name="王教务", role_code="academic_staff", is_active=True, phone="13800002223", email="staff2@edu.cn", managed_college_id=2),
            # 教师
            User(username="teacher1", password_hash=hash_password("123456"), real_name="张明辉", role_code="teacher", is_active=True, phone="13800001111", email="teacher1@edu.cn"),
            User(username="teacher2", password_hash=hash_password("123456"), real_name="刘建华", role_code="teacher", is_active=True, phone="13800001112", email="teacher2@edu.cn"),
            User(username="teacher3", password_hash=hash_password("123456"), real_name="陈美玲", role_code="teacher", is_active=True, phone="13800001113", email="teacher3@edu.cn"),
            User(username="teacher4", password_hash=hash_password("123456"), real_name="赵志远", role_code="teacher", is_active=True, phone="13800001114", email="teacher4@edu.cn"),
            User(username="teacher5", password_hash=hash_password("123456"), real_name="孙丽琴", role_code="teacher", is_active=True, phone="13800001115", email="teacher5@edu.cn"),
            # 学生
            User(username="student1", password_hash=hash_password("123456"), real_name="王小明", role_code="student", is_active=True, phone="13800003333", email="student1@edu.cn"),
            User(username="student2", password_hash=hash_password("123456"), real_name="赵丽", role_code="student", is_active=True, phone="13800003334", email="student2@edu.cn"),
            User(username="student3", password_hash=hash_password("123456"), real_name="陈强", role_code="student", is_active=True, phone="13800003335", email="student3@edu.cn"),
            User(username="student4", password_hash=hash_password("123456"), real_name="林小红", role_code="student", is_active=True, phone="13800003336", email="student4@edu.cn"),
            User(username="student5", password_hash=hash_password("123456"), real_name="黄大力", role_code="student", is_active=True, phone="13800003337", email="student5@edu.cn"),
            User(username="student6", password_hash=hash_password("123456"), real_name="周敏", role_code="student", is_active=True, phone="13800003338", email="student6@edu.cn"),
            User(username="student7", password_hash=hash_password("123456"), real_name="吴昊", role_code="student", is_active=True, phone="13800003339", email="student7@edu.cn"),
            User(username="student8", password_hash=hash_password("123456"), real_name="郑文", role_code="student", is_active=True, phone="13800003340", email="student8@edu.cn"),
            User(username="student9", password_hash=hash_password("123456"), real_name="冯雪", role_code="student", is_active=True, phone="13800003341", email="student9@edu.cn"),
            User(username="student10", password_hash=hash_password("123456"), real_name="蒋波", role_code="student", is_active=True, phone="13800003342", email="student10@edu.cn"),
            User(username="student11", password_hash=hash_password("123456"), real_name="韩雨", role_code="student", is_active=True, phone="13800003343", email="student11@edu.cn"),
            User(username="student12", password_hash=hash_password("123456"), real_name="沈鹏", role_code="student", is_active=True, phone="13800003344", email="student12@edu.cn"),
        ]
        db.add_all(users)
        await db.flush()
        (admin_u, staff_u1, staff_u2,
         t_u1, t_u2, t_u3, t_u4, t_u5,
         s_u1, s_u2, s_u3, s_u4, s_u5, s_u6, s_u7, s_u8, s_u9, s_u10, s_u11, s_u12) = users
        staff_users = [admin_u, staff_u1, staff_u2]

        # ==========================================
        # 3. 学院
        # ==========================================
        from app.model.college import College
        colleges = [
            College(code="CS", name="计算机科学与技术学院", description="涵盖计算机科学、软件工程、人工智能等方向"),
            College(code="EE", name="电子工程学院", description="电子信息、通信工程、自动化等方向"),
            College(code="MATH", name="数学与统计学院", description="数学与应用数学、统计学等方向"),
            College(code="PHY", name="物理学院", description="物理学、应用物理学方向"),
            College(code="FL", name="外国语学院", description="英语、日语、翻译等方向"),
        ]
        db.add_all(colleges)
        await db.flush()
        cs, ee, math, phy, fl = colleges

        # ==========================================
        # 4. 专业
        # ==========================================
        from app.model.major import Major
        majors = [
            Major(code="CS001", name="计算机科学与技术", college_id=cs.id, duration=4, degree="工学学士"),
            Major(code="SE001", name="软件工程", college_id=cs.id, duration=4, degree="工学学士"),
            Major(code="AI001", name="人工智能", college_id=cs.id, duration=4, degree="工学学士"),
            Major(code="EE001", name="电子信息工程", college_id=ee.id, duration=4, degree="工学学士"),
            Major(code="CE001", name="通信工程", college_id=ee.id, duration=4, degree="工学学士"),
            Major(code="MATH01", name="数学与应用数学", college_id=math.id, duration=4, degree="理学学士"),
            Major(code="STAT01", name="统计学", college_id=math.id, duration=4, degree="理学学士"),
            Major(code="PHY001", name="应用物理学", college_id=phy.id, duration=4, degree="理学学士"),
            Major(code="ENG01", name="英语", college_id=fl.id, duration=4, degree="文学学士"),
            Major(code="JPN01", name="日语", college_id=fl.id, duration=4, degree="文学学士"),
        ]
        db.add_all(majors)
        await db.flush()
        (cs_major, se_major, ai_major, ee_major, ce_major,
         math_major, stat_major, phy_major, eng_major, jpn_major) = majors

        # ==========================================
        # 5. 班级
        # ==========================================
        from app.model.class_model import Class
        classes = [
            Class(class_no="CS2101", name="计科2101班", major_id=cs_major.id, grade=2021),
            Class(class_no="SE2102", name="软工2102班", major_id=se_major.id, grade=2021),
            Class(class_no="AI2201", name="人工智能2201班", major_id=ai_major.id, grade=2022),
            Class(class_no="EE2201", name="电子2201班", major_id=ee_major.id, grade=2022),
            Class(class_no="CE2202", name="通信2202班", major_id=ce_major.id, grade=2022),
            Class(class_no="MATH2101", name="数学2101班", major_id=math_major.id, grade=2021),
            Class(class_no="ENG2201", name="英语2201班", major_id=eng_major.id, grade=2022),
            Class(class_no="PHY2101", name="物理2101班", major_id=phy_major.id, grade=2021),
        ]
        db.add_all(classes)
        await db.flush()
        cls1, cls2, cls3, cls4, cls5, cls6, cls7, cls8 = classes

        # ==========================================
        # 6. 教室
        # ==========================================
        from app.model.classroom import Classroom
        classrooms = [
            Classroom(room_no="A101", name="A101多媒体教室", building="教学楼A", type="普通教室", capacity=60, status="可用"),
            Classroom(room_no="A201", name="A201阶梯教室", building="教学楼A", type="阶梯教室", capacity=120, status="可用"),
            Classroom(room_no="B201", name="B201多功能厅", building="教学楼B", type="多媒体教室", capacity=80, status="可用"),
            Classroom(room_no="B301", name="B301语音室", building="教学楼B", type="多媒体教室", capacity=50, status="可用"),
            Classroom(room_no="C301", name="C301计算机实验室", building="实验楼C", type="实验室", capacity=40, status="可用"),
            Classroom(room_no="C302", name="C302电子实验室", building="实验楼C", type="实验室", capacity=35, status="可用"),
        ]
        db.add_all(classrooms)
        await db.flush()
        room1, room2, room3, room4, room5, room6 = classrooms

        # ==========================================
        # 7. 学期
        # ==========================================
        from app.model.semester import Semester
        semesters = [
            Semester(name="2024-2025学年第一学期", start_date="2024-09-01", end_date="2025-01-15", is_current=False),
            Semester(name="2024-2025学年第二学期", start_date="2025-02-16", end_date="2025-07-05", is_current=False),
            Semester(name="2025-2026学年第二学期", start_date="2026-02-16", end_date="2026-07-05", is_current=True),
        ]
        db.add_all(semesters)
        await db.flush()
        sem_old1, sem_old2, sem_current = semesters

        # ==========================================
        # 8. 教师档案
        # ==========================================
        from app.model.teacher import Teacher
        teachers = [
            Teacher(teacher_no="T001", user_id=t_u1.id, college_id=cs.id, title="教授", gender="男"),
            Teacher(teacher_no="T002", user_id=t_u2.id, college_id=ee.id, title="副教授", gender="男"),
            Teacher(teacher_no="T003", user_id=t_u3.id, college_id=math.id, title="讲师", gender="女"),
            Teacher(teacher_no="T004", user_id=t_u4.id, college_id=phy.id, title="副教授", gender="男"),
            Teacher(teacher_no="T005", user_id=t_u5.id, college_id=fl.id, title="讲师", gender="女"),
        ]
        db.add_all(teachers)
        await db.flush()
        tch1, tch2, tch3, tch4, tch5 = teachers

        # ==========================================
        # 9. 学生档案
        # ==========================================
        from app.model.student import Student
        students = [
            Student(student_no="2021001", user_id=s_u1.id, major_id=cs_major.id, class_id=cls1.id, gender="男", enrollment_year=2021),
            Student(student_no="2021002", user_id=s_u2.id, major_id=cs_major.id, class_id=cls1.id, gender="女", enrollment_year=2021),
            Student(student_no="2021003", user_id=s_u3.id, major_id=se_major.id, class_id=cls2.id, gender="男", enrollment_year=2022),
            Student(student_no="2021004", user_id=s_u4.id, major_id=se_major.id, class_id=cls2.id, gender="女", enrollment_year=2021),
            Student(student_no="2022001", user_id=s_u5.id, major_id=ai_major.id, class_id=cls3.id, gender="男", enrollment_year=2022),
            Student(student_no="2022002", user_id=s_u6.id, major_id=ai_major.id, class_id=cls3.id, gender="女", enrollment_year=2022),
            Student(student_no="2022003", user_id=s_u7.id, major_id=ee_major.id, class_id=cls4.id, gender="男", enrollment_year=2022),
            Student(student_no="2022004", user_id=s_u8.id, major_id=ee_major.id, class_id=cls4.id, gender="男", enrollment_year=2022),
            Student(student_no="2022005", user_id=s_u9.id, major_id=ce_major.id, class_id=cls5.id, gender="女", enrollment_year=2022),
            Student(student_no="2021005", user_id=s_u10.id, major_id=math_major.id, class_id=cls6.id, gender="女", enrollment_year=2021),
            Student(student_no="2022006", user_id=s_u11.id, major_id=eng_major.id, class_id=cls7.id, gender="女", enrollment_year=2022),
            Student(student_no="2021006", user_id=s_u12.id, major_id=phy_major.id, class_id=cls8.id, gender="男", enrollment_year=2021),
        ]
        db.add_all(students)
        await db.flush()
        st1, st2, st3, st4, st5, st6, st7, st8, st9, st10, st11, st12 = students

        # ==========================================
        # 10. 课程
        # ==========================================
        from app.model.course import Course
        courses = [
            # 计算机学院课程
            Course(code="CS201", name="数据结构与算法", credit=4, type="必修课", hours=64, teacher_id=tch1.id, college_id=cs.id, semester_id=sem_current.id, max_capacity=60, selected_count=0, description="学习基本数据结构和算法设计"),
            Course(code="CS301", name="操作系统", credit=3, type="必修课", hours=48, teacher_id=tch1.id, college_id=cs.id, semester_id=sem_current.id, max_capacity=60, selected_count=0, description="操作系统原理与实践"),
            Course(code="SE301", name="软件工程", credit=3, type="必修课", hours=48, teacher_id=tch1.id, college_id=cs.id, semester_id=sem_current.id, max_capacity=50, selected_count=0, description="软件开发流程与方法论"),
            Course(code="AI201", name="机器学习导论", credit=3, type="选修课", hours=48, teacher_id=tch1.id, college_id=cs.id, semester_id=sem_current.id, max_capacity=40, selected_count=0, description="机器学习基础算法与应用"),
            # 电子学院课程
            Course(code="EE201", name="数字电路", credit=3, type="必修课", hours=48, teacher_id=tch2.id, college_id=ee.id, semester_id=sem_current.id, max_capacity=55, selected_count=0, description="数字逻辑电路设计"),
            Course(code="EE301", name="信号与系统", credit=4, type="必修课", hours=64, teacher_id=tch2.id, college_id=ee.id, semester_id=sem_current.id, max_capacity=50, selected_count=0, description="连续与离散信号分析"),
            # 数学学院课程
            Course(code="MATH101", name="高等数学选讲", credit=2, type="选修课", hours=32, teacher_id=tch3.id, college_id=math.id, semester_id=sem_current.id, max_capacity=45, selected_count=0, description="高等数学提高与拓展"),
            Course(code="MATH201", name="线性代数", credit=3, type="必修课", hours=48, teacher_id=tch3.id, college_id=math.id, semester_id=sem_current.id, max_capacity=55, selected_count=0, description="矩阵理论与线性空间"),
            # 物理学院课程
            Course(code="PHY201", name="大学物理", credit=4, type="必修课", hours=64, teacher_id=tch4.id, college_id=phy.id, semester_id=sem_current.id, max_capacity=60, selected_count=0, description="力学、热学、电磁学基础"),
            # 外语学院课程
            Course(code="ENG101", name="大学英语（二）", credit=2, type="公共课", hours=32, teacher_id=tch5.id, college_id=fl.id, semester_id=sem_current.id, max_capacity=100, selected_count=0, description="英语听说读写综合训练"),
        ]
        db.add_all(courses)
        await db.flush()
        c1, c2, c3, c4, c5, c6, c7, c8, c9, c10 = courses

        # 更新 selected_count（根据选课数据）
        # 稍后手动更新

        # ==========================================
        # 11. 排课
        # ==========================================
        from app.model.schedule import Schedule
        schedules = [
            # 周一
            Schedule(course_id=c1.id, classroom_id=room3.id, teacher_id=tch1.id, semester_id=sem_current.id, day_of_week=1, period_start=1, period_end=2, week_start=1, week_end=16),
            Schedule(course_id=c5.id, classroom_id=room5.id, teacher_id=tch2.id, semester_id=sem_current.id, day_of_week=1, period_start=3, period_end=4, week_start=1, week_end=16),
            Schedule(course_id=c9.id, classroom_id=room2.id, teacher_id=tch4.id, semester_id=sem_current.id, day_of_week=1, period_start=1, period_end=2, week_start=1, week_end=16),
            # 周二
            Schedule(course_id=c2.id, classroom_id=room1.id, teacher_id=tch1.id, semester_id=sem_current.id, day_of_week=2, period_start=3, period_end=4, week_start=1, week_end=16),
            Schedule(course_id=c7.id, classroom_id=room4.id, teacher_id=tch3.id, semester_id=sem_current.id, day_of_week=2, period_start=1, period_end=2, week_start=1, week_end=16),
            # 周三
            Schedule(course_id=c3.id, classroom_id=room6.id, teacher_id=tch1.id, semester_id=sem_current.id, day_of_week=3, period_start=1, period_end=2, week_start=1, week_end=16),
            Schedule(course_id=c8.id, classroom_id=room1.id, teacher_id=tch3.id, semester_id=sem_current.id, day_of_week=3, period_start=3, period_end=4, week_start=1, week_end=16),
            # 周四
            Schedule(course_id=c6.id, classroom_id=room5.id, teacher_id=tch2.id, semester_id=sem_current.id, day_of_week=4, period_start=1, period_end=2, week_start=1, week_end=16),
            Schedule(course_id=c10.id, classroom_id=room2.id, teacher_id=tch5.id, semester_id=sem_current.id, day_of_week=4, period_start=3, period_end=4, week_start=1, week_end=16),
            # 周五
            Schedule(course_id=c4.id, classroom_id=room3.id, teacher_id=tch1.id, semester_id=sem_current.id, day_of_week=5, period_start=1, period_end=2, week_start=1, week_end=16),
        ]
        db.add_all(schedules)
        await db.flush()

        # ==========================================
        # 12. 选课
        # ==========================================
        from app.model.course_selection import CourseSelection
        # st1(CS2101), st2(CS2101), st3(SE2102), st4(SE2102), st5(AI2201), st6(AI2201)
        # st7(EE2201), st8(EE2201), st9(CE2202), st10(MATH2101), st11(ENG2201), st12(PHY2101)
        selections_data = []
        # CS students: c1 (data structures), c2 (os), c4 (ML), c10 (English)
        for st in [st1, st2]:
            selections_data += [
                CourseSelection(student_id=st.id, course_id=c1.id, semester_id=sem_current.id, status="selected"),
                CourseSelection(student_id=st.id, course_id=c2.id, semester_id=sem_current.id, status="selected"),
                CourseSelection(student_id=st.id, course_id=c4.id, semester_id=sem_current.id, status="selected"),
                CourseSelection(student_id=st.id, course_id=c10.id, semester_id=sem_current.id, status="selected"),
            ]
        # SE students: c3 (SE), c1, c4, c10
        for st in [st3, st4]:
            selections_data += [
                CourseSelection(student_id=st.id, course_id=c3.id, semester_id=sem_current.id, status="selected"),
                CourseSelection(student_id=st.id, course_id=c1.id, semester_id=sem_current.id, status="selected"),
                CourseSelection(student_id=st.id, course_id=c4.id, semester_id=sem_current.id, status="selected"),
                CourseSelection(student_id=st.id, course_id=c10.id, semester_id=sem_current.id, status="selected"),
            ]
        # AI students: c1, c4, c10
        for st in [st5, st6]:
            selections_data += [
                CourseSelection(student_id=st.id, course_id=c1.id, semester_id=sem_current.id, status="selected"),
                CourseSelection(student_id=st.id, course_id=c4.id, semester_id=sem_current.id, status="selected"),
                CourseSelection(student_id=st.id, course_id=c10.id, semester_id=sem_current.id, status="selected"),
            ]
        # EE students: c5 (digital), c6 (signal), c10
        for st in [st7, st8]:
            selections_data += [
                CourseSelection(student_id=st.id, course_id=c5.id, semester_id=sem_current.id, status="selected"),
                CourseSelection(student_id=st.id, course_id=c6.id, semester_id=sem_current.id, status="selected"),
                CourseSelection(student_id=st.id, course_id=c10.id, semester_id=sem_current.id, status="selected"),
            ]
        # CE students: c5, c6, c10
        selections_data += [
            CourseSelection(student_id=st9.id, course_id=c5.id, semester_id=sem_current.id, status="selected"),
            CourseSelection(student_id=st9.id, course_id=c6.id, semester_id=sem_current.id, status="selected"),
            CourseSelection(student_id=st9.id, course_id=c10.id, semester_id=sem_current.id, status="selected"),
        ]
        # MATH students: c7 (advanced math), c8 (linear algebra), c10
        selections_data += [
            CourseSelection(student_id=st10.id, course_id=c7.id, semester_id=sem_current.id, status="selected"),
            CourseSelection(student_id=st10.id, course_id=c8.id, semester_id=sem_current.id, status="selected"),
            CourseSelection(student_id=st10.id, course_id=c10.id, semester_id=sem_current.id, status="selected"),
        ]
        # ENG students: c10
        selections_data += [
            CourseSelection(student_id=st11.id, course_id=c10.id, semester_id=sem_current.id, status="selected"),
        ]
        # PHY students: c9 (physics), c10
        selections_data += [
            CourseSelection(student_id=st12.id, course_id=c9.id, semester_id=sem_current.id, status="selected"),
            CourseSelection(student_id=st12.id, course_id=c10.id, semester_id=sem_current.id, status="selected"),
        ]
        db.add_all(selections_data)

        # 更新课程的 selected_count
        from sqlalchemy import update
        course_counts = {}
        for s in selections_data:
            course_counts[s.course_id] = course_counts.get(s.course_id, 0) + 1
        for cid, cnt in course_counts.items():
            await db.execute(update(Course).where(Course.id == cid).values(selected_count=cnt))

        # ==========================================
        # 13. 考勤（多日期）
        # ==========================================
        from app.model.attendance import Attendance
        dates = ["2026-06-15", "2026-06-16", "2026-06-17", "2026-06-22", "2026-06-23",
                 "2026-06-24", "2026-06-29", "2026-06-30", "2026-07-01", "2026-07-06"]
        attendance_data = []
        # 按课程生成考勤
        course_student_map = {
            c1.id: [st1, st2, st3, st4, st5, st6],  # CS201: 6 students
            c2.id: [st1, st2],                        # CS301: 2 students
            c3.id: [st3, st4],                        # SE301: 2 students
            c4.id: [st1, st2, st3, st4, st5, st6],    # AI201: 6 students
            c5.id: [st7, st8, st9],                   # EE201: 3 students
            c6.id: [st7, st8, st9],                   # EE301: 3 students
            c7.id: [st10],                            # MATH101: 1 student
            c8.id: [st10],                            # MATH201: 1 student
            c9.id: [st12],                            # PHY201: 1 student
            c10.id: [st1, st2, st3, st4, st5, st6, st7, st8, st9, st10, st11, st12],  # ENG101: all
        }
        course_teacher_map = {
            c1.id: tch1, c2.id: tch1, c3.id: tch1, c4.id: tch1, c5.id: tch2,
            c6.id: tch2, c7.id: tch3, c8.id: tch3, c9.id: tch4, c10.id: tch5,
        }
        for cid, st_list in course_student_map.items():
            for i, date in enumerate(dates[:7]):  # 每门课7次考勤
                for st in st_list:
                    # 大多数出勤，偶尔迟到或缺勤
                    import random
                    r = random.random()
                    if r < 0.75:
                        status = "出勤"
                    elif r < 0.90:
                        status = "迟到"
                    else:
                        status = "缺勤"
                    attendance_data.append(
                        Attendance(course_id=cid, student_id=st.id, date=date,
                                   status=status, teacher_id=course_teacher_map[cid].id)
                    )
        db.add_all(attendance_data)

        # ==========================================
        # 14. 成绩
        # ==========================================
        from app.model.score import Score
        score_data = []
        course_student_score = {
            c1.id: [(st1, 90), (st2, 87), (st3, 85), (st4, 78), (st5, 82), (st6, 76)],
            c2.id: [(st1, 78), (st2, 82)],
            c3.id: [(st3, 88), (st4, 91)],
            c4.id: [(st1, 95), (st2, 88), (st3, 72), (st4, 64), (st5, 91), (st6, 83)],
            c5.id: [(st7, 75), (st8, 80), (st9, 68)],
            c6.id: [(st7, 82), (st8, 77), (st9, 70)],
            c7.id: [(st10, 93)],
            c8.id: [(st10, 86)],
            c9.id: [(st12, 79)],
            c10.id: [(st1, 88), (st2, 92), (st3, 85), (st4, 90), (st5, 76), (st6, 82),
                     (st7, 80), (st8, 78), (st9, 74), (st10, 95), (st11, 88), (st12, 72)],
        }
        for cid, entries in course_student_score.items():
            for st, sc in entries:
                score_data.append(
                    Score(student_id=st.id, course_id=cid, semester_id=sem_current.id,
                          score=sc, status="published", teacher_id=course_teacher_map[cid].id)
                )
        # 历史学期成绩（sem_old2 = 2024-2025第二学期）
        historical_scores = [
            Score(student_id=st1.id, course_id=c1.id, semester_id=sem_old2.id, score=85, status="published", teacher_id=tch1.id),
            Score(student_id=st2.id, course_id=c1.id, semester_id=sem_old2.id, score=83, status="published", teacher_id=tch1.id),
            Score(student_id=st1.id, course_id=c2.id, semester_id=sem_old2.id, score=72, status="published", teacher_id=tch1.id),
            Score(student_id=st2.id, course_id=c2.id, semester_id=sem_old2.id, score=80, status="published", teacher_id=tch1.id),
            Score(student_id=st3.id, course_id=c5.id, semester_id=sem_old2.id, score=78, status="published", teacher_id=tch2.id),
            Score(student_id=st4.id, course_id=c5.id, semester_id=sem_old2.id, score=82, status="published", teacher_id=tch2.id),
        ]
        score_data += historical_scores
        db.add_all(score_data)
        await db.flush()

        # ==========================================
        # 15. 成绩变更日志
        # ==========================================
        from app.model.score_log import ScoreLog
        # st3 的 c4 成绩从 68 改为 72
        st3c4 = next(s for s in score_data if s.student_id == st3.id and s.course_id == c4.id)
        db.add(ScoreLog(score_id=st3c4.id, old_score=68, new_score=72, operator_id=admin_u.id))

        # ==========================================
        # 16. 作业
        # ==========================================
        from app.model.assignment import Assignment
        assignments = [
            Assignment(course_id=c1.id, teacher_id=tch1.id, title="二叉树的遍历实现",
                       content="实现前序、中序、后序遍历算法，提交代码和运行结果截图。",
                       deadline="2026-07-10 23:59:00"),
            Assignment(course_id=c1.id, teacher_id=tch1.id, title="图的最短路径算法",
                       content="实现Dijkstra算法并完成实验报告。", deadline="2026-07-20 23:59:00"),
            Assignment(course_id=c2.id, teacher_id=tch1.id, title="进程调度模拟",
                       content="编写程序模拟FCFS和RR调度算法。", deadline="2026-07-08 23:59:00"),
            Assignment(course_id=c3.id, teacher_id=tch1.id, title="需求分析文档",
                       content="对小型图书管理系统进行需求分析并撰写文档。", deadline="2026-07-05 23:59:00"),
            Assignment(course_id=c5.id, teacher_id=tch2.id, title="组合逻辑电路设计",
                       content="设计一个4位加法器电路。", deadline="2026-07-12 23:59:00"),
            Assignment(course_id=c6.id, teacher_id=tch2.id, title="傅里叶变换练习",
                       content="完成5道傅里叶变换计算题。", deadline="2026-07-15 23:59:00"),
            Assignment(course_id=c7.id, teacher_id=tch3.id, title="极限与连续习题",
                       content="完成教材第三章课后习题1-15。", deadline="2026-07-08 23:59:00"),
            Assignment(course_id=c9.id, teacher_id=tch4.id, title="力学实验报告",
                       content="完成碰撞实验报告。", deadline="2026-07-10 23:59:00"),
            Assignment(course_id=c10.id, teacher_id=tch5.id, title="英语作文：My Campus Life",
                       content="写一篇200字的英语作文。", deadline="2026-07-06 23:59:00"),
        ]
        db.add_all(assignments)
        await db.flush()
        asgn1, asgn2, asgn3, asgn4, asgn5, asgn6, asgn7, asgn8, asgn9 = assignments

        # ==========================================
        # 17. 作业提交
        # ==========================================
        from app.model.assignment_submission import AssignmentSubmission
        submissions_data = [
            # asgn1 (二叉树): CS students submitted
            AssignmentSubmission(assignment_id=asgn1.id, student_id=st1.id, content="已完成二叉树遍历实现，代码见附件。", score=95, comment="代码规范，运行正确", submitted_at="2026-07-08 20:30:00", reviewed_at="2026-07-09 10:00:00"),
            AssignmentSubmission(assignment_id=asgn1.id, student_id=st2.id, content="提交三个遍历的实现。", score=92, comment="实现正确，注释详细", submitted_at="2026-07-09 15:00:00", reviewed_at="2026-07-10 09:00:00"),
            AssignmentSubmission(assignment_id=asgn1.id, student_id=st3.id, content="二叉树遍历算法实现完成。", score=88, comment="基本正确，效率可优化", submitted_at="2026-07-10 12:00:00", reviewed_at="2026-07-11 10:00:00"),
            AssignmentSubmission(assignment_id=asgn1.id, student_id=st4.id, content="遍历代码和运行结果已上传。", score=78, comment="中序遍历有bug", submitted_at="2026-07-10 22:00:00", reviewed_at="2026-07-11 14:00:00"),
            AssignmentSubmission(assignment_id=asgn1.id, student_id=st5.id, score=85, comment="良好", submitted_at="2026-07-09 18:00:00", reviewed_at="2026-07-10 16:00:00"),
            AssignmentSubmission(assignment_id=asgn1.id, student_id=st6.id, score=80, comment="功能正确", submitted_at="2026-07-10 19:00:00", reviewed_at="2026-07-11 08:00:00"),
            # asgn3 (进程调度): st1, st2
            AssignmentSubmission(assignment_id=asgn3.id, student_id=st1.id, content="FCFS和RR调度算法已实现。", score=88, comment="逻辑清晰", submitted_at="2026-07-06 22:00:00", reviewed_at="2026-07-07 10:00:00"),
            AssignmentSubmission(assignment_id=asgn3.id, student_id=st2.id, score=90, comment="优秀", submitted_at="2026-07-07 18:00:00", reviewed_at="2026-07-08 09:00:00"),
            # asgn5 (数字电路): EE students
            AssignmentSubmission(assignment_id=asgn5.id, student_id=st7.id, content="4位加法器电路图设计完成。", score=82, comment="电路设计正确", submitted_at="2026-07-11 14:00:00", reviewed_at="2026-07-12 10:00:00"),
            AssignmentSubmission(assignment_id=asgn5.id, student_id=st8.id, score=76, comment="基本正确", submitted_at="2026-07-12 10:00:00"),
            AssignmentSubmission(assignment_id=asgn5.id, student_id=st9.id, content="加法器设计。", score=68, comment="进位逻辑有问题", submitted_at="2026-07-12 20:00:00", reviewed_at="2026-07-13 09:00:00"),
            # asgn7 (极限习题): MATH
            AssignmentSubmission(assignment_id=asgn7.id, student_id=st10.id, content="第三章习题全部完成。", score=96, comment="全对，优秀", submitted_at="2026-07-06 16:00:00", reviewed_at="2026-07-07 10:00:00"),
            # asgn9 (英语作文): all students
            AssignmentSubmission(assignment_id=asgn9.id, student_id=st1.id, content="My Campus Life essay.", score=85, comment="语法正确", submitted_at="2026-07-04 19:00:00", reviewed_at="2026-07-05 14:00:00"),
            AssignmentSubmission(assignment_id=asgn9.id, student_id=st2.id, score=90, comment="表达流畅", submitted_at="2026-07-05 10:00:00", reviewed_at="2026-07-05 15:00:00"),
            AssignmentSubmission(assignment_id=asgn9.id, student_id=st10.id, score=92, comment="用词精准", submitted_at="2026-07-04 22:00:00", reviewed_at="2026-07-05 16:00:00"),
            AssignmentSubmission(assignment_id=asgn9.id, student_id=st12.id, score=78, comment="语法错误较多", submitted_at="2026-07-05 23:00:00", reviewed_at="2026-07-06 10:00:00"),
            # asgn2 (图算法): st1, st3
            AssignmentSubmission(assignment_id=asgn2.id, student_id=st1.id, content="Dijkstra算法实现完成。", score=93, comment="算法实现正确，效率高", submitted_at="2026-07-18 20:00:00", reviewed_at="2026-07-19 10:00:00"),
            AssignmentSubmission(assignment_id=asgn2.id, student_id=st3.id, score=81, comment="思路正确但有边界条件遗漏", submitted_at="2026-07-20 15:00:00", reviewed_at="2026-07-21 09:00:00"),
            # asgn4 (需求分析): st3, st4
            AssignmentSubmission(assignment_id=asgn4.id, student_id=st3.id, content="图书管理系统需求分析文档。", score=87, comment="需求分析全面", submitted_at="2026-07-04 17:00:00", reviewed_at="2026-07-05 14:00:00"),
            AssignmentSubmission(assignment_id=asgn4.id, student_id=st4.id, score=91, comment="文档结构清晰", submitted_at="2026-07-05 09:00:00", reviewed_at="2026-07-05 15:00:00"),
            # asgn6 (傅里叶): st7, st8
            AssignmentSubmission(assignment_id=asgn6.id, student_id=st7.id, content="5道傅里叶变换题目的解答。", score=85, comment="计算正确", submitted_at="2026-07-13 14:00:00", reviewed_at="2026-07-14 10:00:00"),
            AssignmentSubmission(assignment_id=asgn6.id, student_id=st8.id, score=72, comment="第3题有误", submitted_at="2026-07-14 20:00:00", reviewed_at="2026-07-15 09:00:00"),
            # asgn8 (力学实验): st12
            AssignmentSubmission(assignment_id=asgn8.id, student_id=st12.id, content="碰撞实验报告和数据。", score=80, comment="数据分析准确", submitted_at="2026-07-09 11:00:00", reviewed_at="2026-07-10 09:00:00"),
        ]
        db.add_all(submissions_data)

        # ==========================================
        # 18. 假期
        # ==========================================
        from app.model.leave_request import LeaveRequest
        leaves = [
            LeaveRequest(student_id=st1.id, course_id=c1.id, leave_type="病假",
                         leave_date="2026-07-03", reason="感冒发烧需就医",
                         status="pending_staff", teacher_id=tch1.id, teacher_opinion="同意", teacher_at="2026-07-02 15:00:00"),
            LeaveRequest(student_id=st3.id, course_id=c3.id, leave_type="事假",
                         leave_date="2026-07-08", reason="参加竞赛培训",
                         status="pending_teacher"),
            LeaveRequest(student_id=st7.id, course_id=c5.id, leave_type="病假",
                         leave_date="2026-07-05", reason="身体不适",
                         status="rejected", teacher_id=tch2.id, teacher_opinion="无医院证明，不批", teacher_at="2026-07-04 10:00:00"),
            LeaveRequest(student_id=st10.id, course_id=c7.id, leave_type="公假",
                         leave_date="2026-07-12", reason="参加数学建模比赛",
                         status="pending_staff", teacher_id=tch3.id, teacher_opinion="批准参赛", teacher_at="2026-07-10 14:00:00"),
            LeaveRequest(student_id=st2.id, course_id=c1.id, leave_type="事假",
                         leave_date="2026-07-15", reason="家庭事务",
                         status="pending_staff", teacher_id=tch1.id, teacher_opinion="已批", teacher_at="2026-07-14 09:00:00"),
            LeaveRequest(student_id=st8.id, course_id=c6.id, leave_type="病假",
                         leave_date="2026-07-14", reason="急性肠胃炎",
                         status="approved", teacher_id=tch2.id, teacher_opinion="同意", teacher_at="2026-07-13 16:00:00",
                         staff_id=staff_u1.id, staff_opinion="已备案", staff_at="2026-07-13 17:00:00"),
        ]
        db.add_all(leaves)

        # ==========================================
        # 19. 学业预警
        # ==========================================
        from app.model.alert_record import AlertRecord
        alerts = [
            AlertRecord(student_id=st9.id, semester_id=sem_current.id, alert_level="严重",
                        alert_type="多门挂科", description="本学期已有2门课程不及格，出勤率低于60%",
                        attendance_rate=55.0, failed_count=2, status="pending"),
            AlertRecord(student_id=st4.id, semester_id=sem_current.id, alert_level="一般",
                        alert_type="成绩下滑", description="本学期成绩较上学期明显下滑",
                        attendance_rate=88.0, failed_count=0, status="handled",
                        handler_id=admin_u.id, handle_result="已与辅导员沟通，加强学业辅导", handled_at="2026-07-01 10:00:00"),
            AlertRecord(student_id=st12.id, semester_id=sem_current.id, alert_level="严重",
                        alert_type="出勤异常", description="连续缺勤超过3次",
                        attendance_rate=65.0, failed_count=1, status="pending"),
            AlertRecord(student_id=st1.id, semester_id=sem_old2.id, alert_level="一般",
                        alert_type="成绩偏低", description="上学期数据结构成绩偏低，需关注",
                        attendance_rate=85.0, failed_count=0, status="handled",
                        handler_id=staff_u1.id, handle_result="已安排学长辅导", handled_at="2025-07-10 14:00:00"),
        ]
        db.add_all(alerts)

        # ==========================================
        # 20. 社团
        # ==========================================
        from app.model.club import Club
        from app.model.club_member import ClubMember
        clubs = [
            Club(name="计算机协会", description="编程技术交流与竞赛社团", advisor_id=tch1.id),
            Club(name="篮球社", description="篮球运动爱好者社团", advisor_id=tch2.id),
            Club(name="数学建模社", description="数学建模竞赛与学术交流", advisor_id=tch3.id),
            Club(name="英语角", description="英语口语交流与文化活动", advisor_id=tch5.id),
        ]
        db.add_all(clubs)
        await db.flush()
        club_cs, club_bb, club_mm, club_en = clubs

        db.add_all([
            ClubMember(club_id=club_cs.id, student_id=st1.id, role="副社长"),
            ClubMember(club_id=club_cs.id, student_id=st2.id, role="成员"),
            ClubMember(club_id=club_cs.id, student_id=st3.id, role="成员"),
            ClubMember(club_id=club_cs.id, student_id=st5.id, role="成员"),
            ClubMember(club_id=club_bb.id, student_id=st7.id, role="社长"),
            ClubMember(club_id=club_bb.id, student_id=st8.id, role="成员"),
            ClubMember(club_id=club_bb.id, student_id=st9.id, role="成员"),
            ClubMember(club_id=club_mm.id, student_id=st10.id, role="社长"),
            ClubMember(club_id=club_mm.id, student_id=st1.id, role="成员"),
            ClubMember(club_id=club_en.id, student_id=st11.id, role="成员"),
            ClubMember(club_id=club_en.id, student_id=st6.id, role="成员"),
            ClubMember(club_id=club_en.id, student_id=st4.id, role="成员"),
        ])

        # ==========================================
        # 21. 通知
        # ==========================================
        from app.model.notice import Notice
        notices = [
            Notice(title="关于期末考试安排的通知",
                   content="各位同学：本学期期末考试安排已发布，请登录系统查看考试时间和地点，做好复习准备。",
                   publisher_id=staff_u1.id, target_role="all", is_published=True, published_at="2026-06-20 10:00:00"),
            Notice(title="计算机学院学术讲座通知",
                   content="定于7月10日在A201阶梯教室举办《人工智能前沿技术》学术讲座，主讲人：张明辉教授，欢迎广大师生参加。",
                   publisher_id=staff_u1.id, target_role="student", is_published=True, published_at="2026-06-25 08:00:00"),
            Notice(title="关于选课时间调整的通知",
                   content="因系统升级需要，原定6月28日的选课时间调整为6月30日9:00开始，请互相转告。",
                   publisher_id=admin_u.id, target_role="all", is_published=True, published_at="2026-06-27 15:00:00"),
            Notice(title="教师教学工作会议通知",
                   content="定于7月5日14:00在行政楼会议室召开教学工作会议，请全体教师准时参加。",
                   publisher_id=admin_u.id, target_role="teacher", is_published=True, published_at="2026-07-01 09:00:00"),
            Notice(title="暑期安全提示",
                   content="暑期将至，请各位同学注意人身安全、交通安全，合理安排假期时间。留校同学请到辅导员处登记。",
                   publisher_id=staff_u2.id, target_role="all", is_published=False),
            Notice(title="关于论文答辩的通知",
                   content="毕业班同学请注意，毕业论文答辩定于7月3日开始，具体分组安排请查看学院公告栏。",
                   publisher_id=staff_u1.id, target_role="student", is_published=True, published_at="2026-07-01 11:00:00"),
        ]
        db.add_all(notices)

        # ==========================================
        # 22. 用户消息通知
        # ==========================================
        from app.model.user_notification import UserNotification
        notifications = [
            UserNotification(user_id=s_u1.id, title="新作业提醒", content="课程《数据结构与算法》有新作业：二叉树的遍历实现，截止日期7月10日。",
                             notification_type="assignment", related_url="/assignment"),
            UserNotification(user_id=s_u1.id, title="请假审批通过", content="您的7月3日病假申请已通过审批。",
                             notification_type="leave", is_read=True),
            UserNotification(user_id=s_u2.id, title="成绩已发布", content="课程《数据结构与算法》期末成绩已发布，请查看。",
                             notification_type="score", related_url="/score"),
            UserNotification(user_id=s_u1.id, title="新通知", content="关于期末考试安排的通知已发布。",
                             notification_type="notice", related_url="/notice"),
            UserNotification(user_id=t_u1.id, title="新请假审批", content="学生王小明提交了病假申请，请审批。",
                             notification_type="leave", related_url="/leave"),
            UserNotification(user_id=t_u2.id, title="新请假审批", content="学生吴昊提交了病假申请，请审批。",
                             notification_type="leave", related_url="/leave"),
            UserNotification(user_id=s_u10.id, title="作业批改完成", content="课程《高等数学选讲》的作业已批改完成。",
                             notification_type="assignment", is_read=True),
            UserNotification(user_id=s_u7.id, title="请假已拒绝", content="您7月5日的病假申请未通过审批。",
                             notification_type="leave", related_url="/leave"),
            UserNotification(user_id=staff_u1.id, title="考勤异常提醒", content="学生陈强连续缺勤，请关注。",
                             notification_type="alert"),
        ]
        db.add_all(notifications)

        # ==========================================
        # 23. 操作日志
        # ==========================================
        from app.model.user_log import UserLog
        logs = [
            UserLog(user_id=admin_u.id, action="系统初始化", module="系统", detail="安装种子数据", ip_address="127.0.0.1"),
            UserLog(user_id=admin_u.id, action="创建用户", module="用户管理", detail="创建教师用户teacher1", ip_address="127.0.0.1"),
            UserLog(user_id=admin_u.id, action="创建课程", module="课程管理", detail="创建课程《数据结构与算法》CS201", ip_address="127.0.0.1"),
            UserLog(user_id=staff_u1.id, action="发布通知", module="通知管理", detail="发布《期末考试安排通知》", ip_address="127.0.0.1"),
            UserLog(user_id=staff_u1.id, action="审批请假", module="请假管理", detail="审批通过学生王小明病假申请", ip_address="127.0.0.1"),
            UserLog(user_id=tch1.id, action="录入成绩", module="成绩管理", detail="录入数据结构课程学生成绩", ip_address="127.0.0.1"),
            UserLog(user_id=tch1.id, action="发布作业", module="作业管理", detail="发布《二叉树遍历实现》作业", ip_address="127.0.0.1"),
            UserLog(user_id=tch2.id, action="考勤登记", module="考勤管理", detail="登记6月15日数字电路考勤", ip_address="127.0.0.1"),
            UserLog(user_id=s_u1.id, action="提交作业", module="作业管理", detail="提交《二叉树遍历实现》作业", ip_address="127.0.0.1"),
            UserLog(user_id=s_u1.id, action="选课", module="选课管理", detail="选择课程《数据结构与算法》", ip_address="127.0.0.1"),
            UserLog(user_id=admin_u.id, action="编辑用户", module="用户管理", detail="修改student1手机号信息", ip_address="127.0.0.1"),
            UserLog(user_id=staff_u2.id, action="创建学生", module="学生管理", detail="批量导入2022级学生数据", ip_address="127.0.0.1"),
            UserLog(user_id=tch3.id, action="录入成绩", module="成绩管理", detail="录入高等数学选讲成绩", ip_address="127.0.0.1"),
            UserLog(user_id=staff_u1.id, action="处理预警", module="预警管理", detail="处理学生赵丽成绩下滑预警", ip_address="127.0.0.1"),
            UserLog(user_id=s_u7.id, action="请假申请", module="请假管理", detail="提交6月15日病假申请", ip_address="127.0.0.1"),
            UserLog(user_id=tch1.id, action="作业批改", module="作业管理", detail="批改二叉树遍历作业", ip_address="127.0.0.1"),
            UserLog(user_id=admin_u.id, action="系统配置", module="系统", detail="更新学期信息，设置当前学期", ip_address="127.0.0.1"),
        ]
        db.add_all(logs)

        # ==========================================
        # 24. 导入记录
        # ==========================================
        from app.model.import_record import ImportRecord
        imports = [
            ImportRecord(type="student", total_count=50, success_count=48, fail_count=2,
                         fail_detail="行3：学号重复；行15：班级不存在", file_name="2022级新生数据.xlsx",
                         operator_id=staff_u2.id, status="completed"),
            ImportRecord(type="course", total_count=10, success_count=10, fail_count=0,
                         file_name="2025-2026课程数据.xlsx", operator_id=admin_u.id, status="completed"),
            ImportRecord(type="score", total_count=120, success_count=118, fail_count=2,
                         fail_detail="行42：课程不存在；行87：学生不存在", file_name="期末考试导入.xlsx",
                         operator_id=staff_u1.id, status="completed"),
        ]
        db.add_all(imports)

        # ===== 提交 =====
        await db.commit()
        print("=" * 60)
        print("  种子数据插入成功！")
        print("=" * 60)
        print(f"  角色: {len(roles_data)}  / 权限: {len(perms)}")
        print(f"  用户: {len(users)}（管理员1 + 教务2 + 教师5 + 学生12）")
        print(f"  学院: {len(colleges)}  / 专业: {len(majors)}  / 班级: {len(classes)}")
        print(f"  教师: {len(teachers)}  / 学生: {len(students)}")
        print(f"  教室: {len(classrooms)}  / 学期: {len(semesters)}")
        print(f"  课程: {len(courses)}  / 排课: {len(schedules)}")
        print(f"  选课: {len(selections_data)}  / 考勤: {len(attendance_data)}")
        print(f"  成绩: {len(score_data)}（含历史） / 成绩日志: 1")
        print(f"  作业: {len(assignments)}  / 提交: {len(submissions_data)}")
        print(f"  请假: {len(leaves)}  / 预警: {len(alerts)}")
        print(f"  社团: {len(clubs)}  / 成员: 12")
        print(f"  通知: {len(notices)}  / 消息: {len(notifications)}")
        print(f"  日志: {len(logs)}  / 导入记录: {len(imports)}")
        print()
        print("  测试账号（密码统一为123456，admin除外）：")
        print("    管理员: admin / admin123")
        print("    教师: teacher1 ~ teacher5 / 123456")
        print("    教务: staff1, staff2 / 123456")
        print("    学生: student1 ~ student12 / 123456")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
