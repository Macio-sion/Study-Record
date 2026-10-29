# 核心类与属性定义

## 1. 通用模块类

### BaseDAO（通用CRUD基类）
```
@class BaseDAO
  @attr model: SQLAlchemy Model
  @method get_by_id(db, id) -> Optional[Model]
  @method get_all(db, filters, page, page_size) -> Tuple[List[Model], int]
  @method create(db, data) -> Model
  @method update(db, id, data) -> Model
  @method delete(db, id) -> bool
  @method exists(db, filters) -> bool
```

### UnifiedResponse（统一响应封装）
```
@class UnifiedResponse
  @attr code: int = 200
  @attr message: str = "success"
  @attr data: Any = None
  @staticmethod success(data, message) -> JSONResponse
  @staticmethod error(code, message) -> JSONResponse
  @staticmethod paginated(items, total, page, page_size) -> JSONResponse
```

### SecurityUtils（安全工具类）
```
@class SecurityUtils
  @staticmethod hash_password(password: str) -> str
  @staticmethod verify_password(plain, hashed) -> bool
  @staticmethod create_token(user_id, role_code) -> str
  @staticmethod decode_token(token) -> dict
```

---

## 2. 业务模型类（SQLAlchemy ORM）

### User
```
@class User(BaseModel)
  @table: users
  @attr id: int (PK)
  @attr username: str (unique)
  @attr password_hash: str
  @attr role_code: str (admin/academic_staff/teacher/student)
  @attr real_name: str
  @attr phone: str?
  @attr email: str?
  @attr is_active: bool
  @rel teacher: Teacher? (1:1)
  @rel student: Student? (1:1)
```

### Teacher
```
@class Teacher(BaseModel)
  @table: teachers
  @attr id: int (PK)
  @attr teacher_no: str (unique)
  @attr user_id: int (FK → users)
  @attr college_id: int (FK → colleges)
  @attr gender: str (男/女)
  @attr title: str? (教授/副教授/讲师/助教)
  @rel user: User
  @rel college: College
  @rel courses: List[Course]
```

### Student
```
@class Student(BaseModel)
  @table: students
  @attr id: int (PK)
  @attr student_no: str (unique)
  @attr user_id: int (FK → users)
  @attr major_id: int (FK → majors)
  @attr class_id: int (FK → classes)
  @attr gender: str (男/女)
  @attr enrollment_year: int
  @rel user: User
  @rel major: Major
  @rel class_: Class
  @rel selections: List[CourseSelection]
```

### Course
```
@class Course(BaseModel)
  @table: courses
  @attr id: int (PK)
  @attr code: str
  @attr name: str
  @attr semester_id: int (FK → semesters)
  @attr college_id: int (FK → colleges)
  @attr teacher_id: int (FK → teachers)
  @attr credit: Decimal
  @attr max_capacity: int
  @attr selected_count: int (默认0)
  @attr hours: int
  @attr type: str (必修/选修)
  @attr version: int (乐观锁)
  @rel semester: Semester
  @rel teacher: Teacher
  @rel schedules: List[Schedule]
  @rel selections: List[CourseSelection]
```

### Schedule
```
@class Schedule(BaseModel)
  @table: schedules
  @attr id: int (PK)
  @attr course_id: int (FK)
  @attr classroom_id: int (FK)
  @attr teacher_id: int (FK)
  @attr semester_id: int (FK)
  @attr week_start: int
  @attr week_end: int
  @attr day_of_week: int (1-7)
  @attr period_start: int
  @attr period_end: int
  @rel course: Course
  @rel classroom: Classroom
```

### CourseSelection
```
@class CourseSelection(BaseModel)
  @table: course_selections
  @attr id: int (PK)
  @attr student_id: int (FK)
  @attr course_id: int (FK)
  @attr semester_id: int (FK)
  @attr selected_at: datetime
  @attr status: str (selected/dropped)
  @rel student: Student
  @rel course: Course
```

### Attendance
```
@class Attendance(BaseModel)
  @table: attendances
  @attr id: int (PK)
  @attr course_id: int (FK)
  @attr student_id: int (FK)
  @attr teacher_id: int (FK)
  @attr date: date
  @attr status: str (present/late/early_leave/absent)
  @attr remark: str?
  @rel course: Course
  @rel student: Student
```

### Score
```
@class Score(BaseModel)
  @table: scores
  @attr id: int (PK)
  @attr student_id: int (FK)
  @attr course_id: int (FK)
  @attr semester_id: int (FK)
  @attr score: Decimal
  @attr status: str (draft/published/locked)
  @attr teacher_id: int (FK)
  @rel course: Course
  @rel student: Student
  @rel logs: List[ScoreLog]
```

### Assignment
```
@class Assignment(BaseModel)
  @table: assignments
  @attr id: int (PK)
  @attr course_id: int (FK)
  @attr teacher_id: int (FK)
  @attr title: str
  @attr content: str
  @attr file_path: str?
  @attr deadline: datetime
  @rel course: Course
  @rel submissions: List[AssignmentSubmission]
```

### LeaveRequest
```
@class LeaveRequest(BaseModel)
  @table: leave_requests
  @attr id: int (PK)
  @attr student_id: int (FK)
  @attr course_id: int (FK)
  @attr leave_type: str
  @attr leave_date: date
  @attr reason: str
  @attr status: str (pending_teacher/pending_staff/approved/rejected)
  @attr teacher_id: int?
  @attr teacher_opinion: str?
  @attr staff_id: int?
  @attr staff_opinion: str?
```

### AlertRecord
```
@class AlertRecord(BaseModel)
  @table: alert_records
  @attr id: int (PK)
  @attr student_id: int (FK)
  @attr semester_id: int (FK)
  @attr alert_level: str (yellow/orange/red)
  @attr attendance_rate: Decimal?
  @attr failed_count: int?
  @attr status: str (pending/processing/resolved)
  @attr handler_id: int?
  @attr handle_result: str?
```

---

## 3. 服务层类

### SelectionService（选课服务 - 高并发）
```
@class SelectionService
  @attr redis_client: Redis
  @attr rate_limiter: RateLimiter
  @method enroll(student_id, course_id) -> Result
    - 限流检查
    - 冲突检测（check_time_conflict）
    - Redis缓存容量检查
    - 乐观锁扣减容量
    - 写入选课记录
  @method drop(student_id, course_id) -> Result
  @method get_available_courses(student_id, semester_id) -> List[Course]
  @method check_time_conflict(student_id, course_id) -> bool
  @method get_course_capacity_from_cache(course_id) -> int
```

### ScheduleService（排课服务）
```
@class ScheduleService
  @method generate_schedule(semester_id, course_ids) -> str (task_id)
  @method auto_schedule(courses, classrooms) -> List[Schedule]
  @method check_conflicts(schedule) -> List[str] (冲突信息)
  @method check_teacher_conflict(teacher_id, week, day, period) -> bool
  @method check_classroom_conflict(classroom_id, week, day, period) -> bool
  @method check_class_conflict(class_id, week, day, period) -> bool (需JOIN查询)
  @method manual_add(schedule_data) -> Schedule
  @method get_teacher_timetable(teacher_id, week) -> List[Schedule]
  @method get_student_timetable(student_id, week) -> List[Schedule]
```

### ImportService（批量导入服务）
```
@class ImportService
  @method import_teachers(file) -> str (task_id)
  @method import_students(file) -> str (task_id)
  @method process_teacher_import(rows) -> ImportResult
    - 逐行校验（工号唯一、必填字段）
    - 事务创建 user + teacher
    - 返回成功/失败统计
  @method process_student_import(rows) -> ImportResult
```

### AttendanceService（考勤统计服务）
```
@class AttendanceService
  @method get_course_attendance_rate(course_id) -> dict
  @method get_student_attendance_rate(student_id) -> dict
  @method get_overview(semester_id) -> dict
  @method mark_attendance(course_id, date, records) -> bool
```

### AlertService（学业预警服务）
```
@class AlertService
  @method generate_alerts(semester_id) -> List[AlertRecord]
  @method scan_attendance_warnings(semester_id, threshold) -> List[int] (student_ids)
  @method scan_score_warnings(semester_id, threshold) -> List[int]
  @method send_alert_notification(student_ids) -> bool
```
