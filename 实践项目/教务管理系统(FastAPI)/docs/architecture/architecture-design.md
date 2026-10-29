# 技术架构设计文档

## 1. 文档信息

| 项目 | 内容 |
| :--- | :--- |
| 文档版本 | v1.0 |
| 创建日期 | 2026-07-22 |
| 对应PRD版本 | v1.0 |

---

## 2. 系统模块划分

```mermaid
graph TB
    subgraph Frontend["前端层 (Vue3 + ElementPlus)"]
        direction TB
        Router["Vue Router\n路由守卫 + 动态菜单"]
        Store["Pinia Store\n全局状态管理"]
        Views["页面组件\n17个模块视图"]
        Comps["通用组件\n表格/表单/图表"]
        API["Axios封装\n请求拦截/响应处理"]
    end

    subgraph Gateway["网关层"]
        Nginx["Nginx\n反向代理 + 静态资源"]
    end

    subgraph Backend["后端层 (FastAPI)"]
        direction TB
        MW["中间件层\nCORS / JWT认证 / 限流 / 日志"]
        Router_BE["路由层\n17个模块路由注册"]
        Controller["Controller层\n请求参数校验 / 响应封装"]
        Service["Service层\n业务逻辑编排"]
        DAO["DAO层\n数据访问 + 事务管理"]
        Task["Celery异步任务\n排课计算 / 批量导入"]
    end

    subgraph Data["数据层"]
        MySQL[("MySQL 8.0\n关系型数据存储")]
        Redis[("Redis 7\n缓存 / 限流 / 任务队列")]
        FS["文件存储\n作业附件 / 头像"]
    end

    Frontend --> Nginx
    Nginx --> Backend
    Backend --> Data
```

---

## 3. 项目目录结构

```
教务管理系统/
├── backend/                          # 后端项目根目录
│   ├── app/
│   │   ├── main.py                   # FastAPI 应用入口
│   │   ├── config.py                 # 配置管理（环境变量）
│   │   ├── database.py               # 数据库连接池 + Session
│   │   ├── common/                   # 通用模块
│   │   │   ├── response.py           # 统一响应封装
│   │   │   ├── exception.py          # 全局异常处理
│   │   │   ├── middleware.py         # 中间件（JWT/CORS/日志）
│   │   │   └── security.py          # JWT生成/校验、bcrypt
│   │   ├── model/                    # 数据库模型（SQLAlchemy ORM）
│   │   │   ├── user.py
│   │   │   ├── college.py
│   │   │   ├── major.py
│   │   │   ├── teacher.py
│   │   │   ├── student.py
│   │   │   ├── class_.py
│   │   │   ├── course.py
│   │   │   ├── semester.py
│   │   │   ├── classroom.py
│   │   │   ├── schedule.py
│   │   │   ├── course_selection.py
│   │   │   ├── attendance.py
│   │   │   ├── score.py
│   │   │   ├── assignment.py
│   │   │   ├── leave_request.py
│   │   │   ├── alert.py
│   │   │   ├── club.py
│   │   │   └── notice.py
│   │   ├── dto/                      # 数据传输对象（Pydantic Schema）
│   │   │   ├── user_schema.py
│   │   │   ├── college_schema.py
│   │   │   ├── ...（每个模块对应一个schema文件）
│   │   │   └── common_schema.py      # 分页、通用查询
│   │   ├── router/                   # 路由层（Controller）
│   │   │   ├── auth_router.py
│   │   │   ├── user_router.py
│   │   │   ├── college_router.py
│   │   │   ├── ...（每个模块对应一个router文件）
│   │   │   └── dashboard_router.py
│   │   ├── service/                  # 业务逻辑层
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── college_service.py
│   │   │   ├── ...（每个模块对应一个service文件）
│   │   │   ├── schedule_service.py   # 排课算法
│   │   │   └── selection_service.py  # 选课高并发逻辑
│   │   ├── dao/                      # 数据访问层
│   │   │   ├── user_dao.py
│   │   │   ├── college_dao.py
│   │   │   ├── ...（每个模块对应一个dao文件）
│   │   │   └── base_dao.py          # 通用CRUD基类
│   │   ├── utils/                    # 工具模块
│   │   │   ├── excel_parser.py       # Excel解析
│   │   │   ├── file_upload.py        # 文件上传
│   │   │   ├── redis_client.py       # Redis客户端
│   │   │   └── rate_limiter.py       # 限流器
│   │   └── tasks/                    # Celery异步任务
│   │       ├── __init__.py
│   │       ├── celery_app.py         # Celery配置
│   │       ├── schedule_task.py      # 排课任务
│   │       └── import_task.py        # 批量导入任务
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic/                      # 数据库迁移
│       ├── env.py
│       └── versions/
│
├── frontend/                         # 前端项目根目录
│   ├── src/
│   │   ├── main.js                   # Vue应用入口
│   │   ├── App.vue                   # 根组件
│   │   ├── router/
│   │   │   ├── index.js              # 路由配置
│   │   │   └── permission.js         # 路由守卫 + 动态路由
│   │   ├── store/
│   │   │   ├── user.js               # 用户状态（登录/角色/权限）
│   │   │   ├── app.js                # 应用状态（侧边栏/主题）
│   │   │   └── modules/             # 各模块状态
│   │   ├── api/                      # 后端接口调用
│   │   │   ├── request.js            # Axios封装（拦截器）
│   │   │   ├── auth.js
│   │   │   ├── user.js
│   │   │   ├── college.js
│   │   │   └── ...（每个模块一个api文件）
│   │   ├── views/                    # 页面组件
│   │   │   ├── login/
│   │   │   ├── dashboard/
│   │   │   ├── system/              # 系统管理
│   │   │   ├── college/             # 学院专业
│   │   │   ├── teacher/
│   │   │   ├── student/
│   │   │   ├── course/
│   │   │   ├── classroom/
│   │   │   ├── schedule/
│   │   │   ├── selection/
│   │   │   ├── timetable/
│   │   │   ├── attendance/
│   │   │   ├── score/
│   │   │   ├── assignment/
│   │   │   ├── leave/
│   │   │   ├── alert/
│   │   │   ├── club/
│   │   │   └── notice/
│   │   ├── components/               # 通用组件
│   │   │   ├── layout/
│   │   │   ├── TableEx.vue
│   │   │   ├── FormEx.vue
│   │   │   └── ChartEx.vue
│   │   ├── utils/
│   │   │   ├── auth.js              # Token管理
│   │   │   └── validate.js          # 表单校验规则
│   │   └── assets/                   # 静态资源
│   ├── vite.config.js
│   ├── index.html
│   └── package.json
│
├── docs/                             # 文档
├── tests/                            # 测试
├── .gitignore
└── README.md
```

---

## 4. 数据库ER图

```mermaid
erDiagram
    users ||--o| teachers : "1:1"
    users ||--o| students : "1:1"
    users {
        int id PK
        varchar username UK
        varchar password_hash
        varchar role_code
        varchar real_name
        varchar phone
        varchar email
        tinyint is_active
    }

    colleges ||--o{ majors : "1:N"
    colleges {
        int id PK
        varchar code UK
        varchar name
        varchar description
    }

    majors ||--o{ students : "1:N"
    majors ||--o{ classes : "1:N"
    majors {
        int id PK
        varchar code UK
        varchar name
        int college_id FK
        int duration
        varchar degree
    }

    classes ||--o{ students : "1:N"
    classes {
        int id PK
        varchar class_no UK
        varchar name
        int major_id FK
        int advisor_id FK
        int grade
    }

    teachers {
        int id PK
        varchar teacher_no UK
        int user_id FK
        int college_id FK
        varchar gender
        varchar title
    }

    students {
        int id PK
        varchar student_no UK
        int user_id FK
        int major_id FK
        int class_id FK
        varchar gender
        int enrollment_year
    }

    semesters ||--o{ courses : "1:N"
    semesters ||--o{ schedules : "1:N"
    semesters ||--o{ course_selections : "1:N"
    semesters ||--o{ scores : "1:N"
    semesters {
        int id PK
        varchar name
        date start_date
        date end_date
        tinyint is_current
    }

    colleges ||--o{ courses : "1:N"
    teachers ||--o{ courses : "1:N"
    courses ||--o{ schedules : "1:N"
    courses ||--o{ course_selections : "1:N"
    courses ||--o{ scores : "1:N"
    courses ||--o{ attendances : "1:N"
    courses ||--o{ assignments : "1:N"
    courses ||--o{ leave_requests : "1:N"
    courses {
        int id PK
        varchar code
        varchar name
        int semester_id FK
        int college_id FK
        int teacher_id FK
        decimal credit
        int max_capacity
        int hours
        varchar type
        varchar description
        int selected_count
        int version
    }

    classrooms ||--o{ schedules : "1:N"
    classrooms {
        int id PK
        varchar room_no UK
        varchar name
        varchar building
        int capacity
        varchar type
        varchar status
    }

    schedules {
        int id PK
        int course_id FK
        int classroom_id FK
        int teacher_id FK
        int semester_id FK
        int week_start
        int week_end
        int day_of_week
        int period_start
        int period_end
    }

    students ||--o{ course_selections : "1:N"
    course_selections {
        int id PK
        int student_id FK
        int course_id FK
        int semester_id FK
        datetime selected_at
        varchar status
    }

    students ||--o{ attendances : "1:N"
    teachers ||--o{ attendances : "1:N"
    attendances {
        int id PK
        int course_id FK
        int student_id FK
        int teacher_id FK
        date date
        varchar status
        varchar remark
    }

    students ||--o{ scores : "1:N"
    teachers ||--o{ scores : "1:N"
    scores {
        int id PK
        int student_id FK
        int course_id FK
        int semester_id FK
        decimal score
        varchar status
        int teacher_id FK
    }

    scores ||--o{ score_logs : "1:N"
    score_logs {
        int id PK
        int score_id FK
        decimal old_score
        decimal new_score
        int operator_id
    }

    assignments ||--o{ assignment_submissions : "1:N"
    assignments {
        int id PK
        int course_id FK
        int teacher_id FK
        varchar title
        text content
        varchar file_path
        datetime deadline
    }

    students ||--o{ assignment_submissions : "1:N"
    assignment_submissions {
        int id PK
        int assignment_id FK
        int student_id FK
        text content
        varchar file_path
        decimal score
        varchar comment
        datetime submitted_at
        datetime reviewed_at
    }

    students ||--o{ leave_requests : "1:N"
    teachers ||--o{ leave_requests : "1:N"
    users ||--o{ leave_requests : "审批人"
    leave_requests {
        int id PK
        int student_id FK
        int course_id FK
        varchar leave_type
        date leave_date
        text reason
        varchar status
        int teacher_id FK
        varchar teacher_opinion
        datetime teacher_at
        int staff_id FK
        varchar staff_opinion
        datetime staff_at
    }

    teachers ||--o{ clubs : "1:N"
    clubs ||--o{ club_members : "1:N"
    clubs {
        int id PK
        varchar name UK
        varchar description
        int advisor_id FK
    }

    students ||--o{ club_members : "1:N"
    club_members {
        int id PK
        int club_id FK
        int student_id FK
        varchar role
        datetime joined_at
    }

    alert_records {
        int id PK
        int student_id FK
        int semester_id FK
        varchar alert_level
        decimal attendance_rate
        int failed_count
        varchar status
        int handler_id
        varchar handle_result
        datetime handled_at
    }

    notices {
        int id PK
        varchar title
        text content
        int publisher_id FK
        varchar visible_to
        tinyint is_published
        datetime published_at
    }
```

### 索引策略

| 表名 | 索引名 | 类型 | 字段 | 用途 |
| :--- | :--- | :--- | :--- | :--- |
| users | uk_username | UNIQUE | username | 登录查询 |
| users | idx_role_code | NORMAL | role_code | 按角色筛选 |
| courses | idx_semester | NORMAL | semester_id | 按学期查询 |
| courses | idx_teacher | NORMAL | teacher_id | 教师授课查询 |
| schedules | idx_course | NORMAL | course_id | 排课查询 |
| schedules | uk_slot | UNIQUE | classroom_id, semester_id, week_start, day_of_week, period_start | 教室冲突检测 |
| schedules | idx_teacher_week | NORMAL | teacher_id, semester_id, week_start | 教师课表 |
| course_selections | uk_student_course | UNIQUE | student_id, course_id, semester_id | 防重复选课 |
| course_selections | idx_student | NORMAL | student_id, semester_id | 学生课表 |
| attendances | uk_course_student_date | UNIQUE | course_id, student_id, date | 防重复点名 |
| scores | uk_student_course_semester | UNIQUE | student_id, course_id, semester_id | 防重复录入 |
| assignment_submissions | uk_assignment_student | UNIQUE | assignment_id, student_id | 防重复提交 |
| club_members | uk_club_student | UNIQUE | club_id, student_id | 防重复加入 |
```

### 外键关系汇总

| 子表 | 外键字段 | 父表 | 关系 | 级联策略 |
| :--- | :--- | :--- | :--- | :--- |
| teachers | user_id | users | 1:1 | CASCADE |
| students | user_id | users | 1:1 | CASCADE |
| majors | college_id | colleges | N:1 | RESTRICT |
| classes | major_id | majors | N:1 | RESTRICT |
| classes | advisor_id | teachers | N:1 | SET NULL |
| students | major_id | majors | N:1 | RESTRICT |
| students | class_id | classes | N:1 | RESTRICT |
| courses | semester_id | semesters | N:1 | RESTRICT |
| courses | college_id | colleges | N:1 | RESTRICT |
| courses | teacher_id | teachers | N:1 | RESTRICT |
| schedules | course_id | courses | N:1 | CASCADE |
| schedules | classroom_id | classrooms | N:1 | RESTRICT |
| course_selections | student_id | students | N:1 | CASCADE |
| course_selections | course_id | courses | N:1 | CASCADE |
| attendances | course_id | courses | N:1 | CASCADE |
| attendances | student_id | students | N:1 | CASCADE |
| scores | student_id | students | N:1 | CASCADE |
| scores | course_id | courses | N:1 | CASCADE |
| score_logs | score_id | scores | N:1 | CASCADE |
| assignments | course_id | courses | N:1 | CASCADE |
| assignment_submissions | assignment_id | assignments | N:1 | CASCADE |
| assignment_submissions | student_id | students | N:1 | CASCADE |
| leave_requests | student_id | students | N:1 | CASCADE |
| leave_requests | course_id | courses | N:1 | CASCADE |
| clubs | advisor_id | teachers | N:1 | RESTRICT |
| club_members | club_id | clubs | N:1 | CASCADE |
| club_members | student_id | students | N:1 | CASCADE |
| alert_records | student_id | students | N:1 | CASCADE |
| alert_records | semester_id | semesters | N:1 | RESTRICT |
| notices | publisher_id | users | N:1 | RESTRICT |
