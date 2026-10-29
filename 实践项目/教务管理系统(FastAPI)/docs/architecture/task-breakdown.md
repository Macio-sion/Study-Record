# 原子化任务拆解清单

## 总览

| 阶段 | 任务数 | 范围 | 优先级 |
| :--- | :---: | :--- | :---: |
| 第1阶段：项目骨架 | 4 | 目录结构、数据库、配置文件、迁移脚本 | P0 |
| 第2阶段：公共模块 | 4 | 统一响应、异常处理、JWT认证、RBAC中间件 | P0 |
| 第3阶段：P0基础实体 | 7 | 学院专业、教师、学生、班级、课程、教室、学期 | P0 |
| 第4阶段：P0核心业务 | 8 | 排课、选课、课表、点名、考勤、成绩、作业 | P0 |
| 第5阶段：P1辅助增强 | 4 | 请假审批、学业预警、社团、通知公告 | P1 |
| 第6阶段：P2收尾 | 3 | 操作日志、报表导出、前端联调+集成测试 | P2 |
| **合计** | **30** | | |

## Git分支策略

| 分支 | 用途 | 说明 |
| :--- | :--- | :--- |
| `main` | 稳定版本 | 仅接受dev合并，合并前所有测试通过 |
| `dev` | 开发+测试 | 每个任务完成后提交到dev，测试通过后合并到main |

## 任务详情

### Task-01：创建后端项目骨架
- **优先级**：P0
- **输入依赖**：无
- **输出产物**：`backend/` 目录结构、`main.py`、`config.py`、`database.py`、`requirements.txt`
- **验收标准**：(1) FastAPI 应用可启动 (2) Swagger `/docs` 可访问 (3) 数据库连接池配置正确 (4) `.env` 环境变量加载正常

### Task-02：创建前端项目骨架
- **优先级**：P0
- **输入依赖**：无
- **输出产物**：`frontend/` 目录结构、`vite.config.js`、`App.vue`、`router/index.js`、`store/`、`api/request.js`、`Layout.vue`
- **验收标准**：(1) `npm run dev` 可启动 (2) 登录页可访问 (3) 基础Layout框架渲染 (4) Axios封装含拦截器

### Task-03：数据库初始化 + Alembic迁移框架
- **优先级**：P0
- **输入依赖**：Task-01
- **输出产物**：`alembic/` 目录、初始迁移脚本（创建所有26张表）、数据库连接验证
- **验收标准**：(1) `alembic upgrade head` 成功创建所有表 (2) 表结构与PRD数据字典一致 (3) 索引和外键正确创建

### Task-04：创建所有SQLAlchemy ORM模型
- **优先级**：P0
- **输入依赖**：Task-03
- **输出产物**：`backend/app/model/` 下所有16+个模型文件、`base.py` 基类
- **验收标准**：(1) 所有26张表有对应ORM模型 (2) 关系映射正确 (3) 模型可正常导入无报错

### Task-05：统一响应封装 + 全局异常处理中间件
- **优先级**：P0
- **输入依赖**：Task-01
- **输出产物**：`common/response.py`、`common/exception.py`、`common/middleware.py`
- **验收标准**：(1) 统一响应格式 `{code, message, data}` (2) 分页响应含 `total, page, page_size` (3) 异常自动捕获 (4) CORS中间件

### Task-06：JWT认证 + bcrypt密码加密
- **优先级**：P0
- **输入依赖**：Task-04、Task-05
- **输出产物**：`common/security.py`、`dto/user_schema.py`
- **验收标准**：(1) POST /auth/login 返回JWT (2) Token过期返回401 (3) bcrypt密码哈希

### Task-07：RBAC权限拦截器 + 角色装饰器
- **优先级**：P0
- **输入依赖**：Task-06
- **输出产物**：`common/permission.py`、`dependencies/`
- **验收标准**：(1) `@require_role()` 装饰器正确拦截 (2) 越权返回403 (3) 无认证返回401

### Task-08：Pydantic Schema定义（全部DTO）
- **优先级**：P0
- **输入依赖**：Task-04
- **输出产物**：`backend/app/dto/` 下所有Schema文件
- **验收标准**：(1) 每个模块有完整CRUD Schema (2) 分页查询参数模型可用 (3) 字段校验规则正确

### Task-09：用户管理（系统管理模块）
- **优先级**：P0
- **输入依赖**：Task-06、Task-07、Task-08
- **输出产物**：`router/auth_router.py`、`router/user_router.py`、`service/auth_service.py`、`service/user_service.py`、`dao/user_dao.py` + `dao/base_dao.py`

### Task-10：学院与专业管理
- **优先级**：P0
- **输入依赖**：Task-07、Task-08
- **输出产物**：`router/college_router.py`、`service/college_service.py`、`dao/college_dao.py`

### Task-11：教师管理 + 批量导入
- **优先级**：P0
- **输入依赖**：Task-07、Task-08、Task-10
- **输出产物**：`router/teacher_router.py`、`service/teacher_service.py`、`dao/teacher_dao.py`、`utils/excel_parser.py`

### Task-12：学生管理 + 班级管理 + 批量导入
- **优先级**：P0
- **输入依赖**：Task-07、Task-08、Task-10
- **输出产物**：`router/student_router.py`、`router/class_router.py`、`service/student_service.py`、`dao/student_dao.py`

### Task-13：课程管理 + 学期管理
- **优先级**：P0
- **输入依赖**：Task-07、Task-08、Task-10、Task-11
- **输出产物**：`router/course_router.py`、`router/semester_router.py`、`service/course_service.py`、`dao/course_dao.py`

### Task-14：教室管理
- **优先级**：P0
- **输入依赖**：Task-07、Task-08
- **输出产物**：`router/classroom_router.py`、`service/classroom_service.py`、`dao/classroom_dao.py`

### Task-15：P0基础实体单元测试
- **优先级**：P0
- **输入依赖**：Task-09 ~ Task-14
- **输出产物**：`tests/unit/test_user.py`、`tests/unit/test_college.py`、`tests/unit/test_teacher.py`、`tests/unit/test_student.py`、`tests/unit/test_course.py`、`tests/unit/test_classroom.py`、`tests/conftest.py`

### Task-16：排课管理
- **优先级**：P0
- **输入依赖**：Task-07、Task-08、Task-13、Task-14
- **输出产物**：`router/schedule_router.py`、`service/schedule_service.py`、`dao/schedule_dao.py`、`tasks/celery_app.py`、`tasks/schedule_task.py`

### Task-17：选课管理（高并发设计）
- **优先级**：P0
- **输入依赖**：Task-07、Task-08、Task-13、Task-16
- **输出产物**：`router/selection_router.py`、`service/selection_service.py`、`dao/selection_dao.py`、`utils/redis_client.py`、`utils/rate_limiter.py`

### Task-18：课表系统
- **优先级**：P0
- **输入依赖**：Task-16、Task-17
- **输出产物**：`router/timetable_router.py`、`service/timetable_service.py`、前端课表视图组件

### Task-19：点名系统
- **优先级**：P0
- **输入依赖**：Task-07、Task-08、Task-13
- **输出产物**：`router/attendance_router.py`、`service/attendance_service.py`、`dao/attendance_dao.py`

### Task-20：考勤统计（可视化）
- **优先级**：P0
- **输入依赖**：Task-19
- **输出产物**：`router/attendance_stats_router.py`、`service/attendance_stats_service.py`、前端ECharts图表组件

### Task-21：成绩管理
- **优先级**：P0
- **输入依赖**：Task-07、Task-08、Task-13、Task-17
- **输出产物**：`router/score_router.py`、`service/score_service.py`、`dao/score_dao.py`

### Task-22：作业管理
- **优先级**：P0
- **输入依赖**：Task-07、Task-08、Task-13
- **输出产物**：`router/assignment_router.py`、`service/assignment_service.py`、`dao/assignment_dao.py`、`utils/file_upload.py`

### Task-23：P0核心业务单元测试
- **优先级**：P0
- **输入依赖**：Task-16 ~ Task-22
- **输出产物**：`tests/unit/test_schedule.py`、`tests/unit/test_selection.py`、`tests/unit/test_attendance.py`、`tests/unit/test_score.py`、`tests/unit/test_assignment.py`

### Task-24：请假审批
- **优先级**：P1
- **输入依赖**：Task-07、Task-08、Task-13
- **输出产物**：`router/leave_router.py`、`service/leave_service.py`、`dao/leave_dao.py`

### Task-25：学业预警
- **优先级**：P1
- **输入依赖**：Task-20、Task-21、Celery
- **输出产物**：`router/alert_router.py`、`service/alert_service.py`、`dao/alert_dao.py`、`tasks/alert_task.py`

### Task-26：社团管理
- **优先级**：P1
- **输入依赖**：Task-07、Task-08、Task-11、Task-12
- **输出产物**：`router/club_router.py`、`service/club_service.py`、`dao/club_dao.py`

### Task-27：通知公告
- **优先级**：P1
- **输入依赖**：Task-07、Task-08
- **输出产物**：`router/notice_router.py`、`service/notice_service.py`、`dao/notice_dao.py`

### Task-28：操作日志 + 数据导出
- **优先级**：P2
- **输入依赖**：所有业务模块
- **输出产物**：`dao/log_dao.py`、`utils/excel_writer.py`

### Task-29：前端UI打磨 + 联调
- **优先级**：P2
- **输入依赖**：所有后端任务
- **输出产物**：17个模块前端页面组件

### Task-30：集成测试 + 冒烟测试
- **优先级**：P2
- **输入依赖**：Task-29
- **输出产物**：`tests/integration/` 集成测试、冒烟测试报告
