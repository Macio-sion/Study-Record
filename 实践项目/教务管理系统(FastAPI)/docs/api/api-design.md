# API接口设计文档

## 1. 设计规范

| 项目 | 规范 |
| :--- | :--- |
| 协议 | HTTPS（开发环境 HTTP） |
| 基础路径 | `/api/v1` |
| 认证方式 | JWT Bearer Token（Header: `Authorization: Bearer <token>`） |
| 响应格式 | JSON，统一封装 `{code, message, data}` |
| 请求格式 | JSON（GET 使用 Query String，上传使用 multipart/form-data） |
| 分页 | `page` + `page_size`，默认 page=1, page_size=20 |
| 日期格式 | ISO 8601（`YYYY-MM-DD` / `YYYY-MM-DDTHH:mm:ss`） |
| 状态码 | 200/201/204 成功，400/401/403/404/409/429 客户端错误，500 服务器错误 |

---

## 2. 统一响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### 分页响应
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "课程名额已满",
  "data": null
}
```

---

## 3. 接口清单

### 3.1 认证模块 `/api/v1/auth`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| POST | `/auth/login` | 用户登录 | 公开 |
| POST | `/auth/logout` | 退出登录 | 登录用户 |
| GET | `/auth/me` | 获取当前用户信息 | 登录用户 |
| PUT | `/auth/me` | 修改个人信息 | 登录用户 |
| PUT | `/auth/password` | 修改密码 | 登录用户 |

#### POST `/auth/login`
**Request**:
```json
{
  "username": "admin",
  "password": "123456"
}
```
**Response**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "username": "admin",
      "role_code": "admin",
      "real_name": "系统管理员"
    }
  }
}
```

---

### 3.2 用户管理 `/api/v1/users`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/users` | 用户列表（分页+筛选） | admin |
| POST | `/users` | 创建用户 | admin |
| GET | `/users/{id}` | 用户详情 | admin |
| PUT | `/users/{id}` | 更新用户 | admin |
| PUT | `/users/{id}/status` | 启用/禁用用户 | admin |

---

### 3.3 学院管理 `/api/v1/colleges`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/colleges` | 学院列表 | admin, staff |
| POST | `/colleges` | 创建学院 | admin, staff |
| GET | `/colleges/{id}` | 学院详情 | admin, staff |
| PUT | `/colleges/{id}` | 更新学院 | admin, staff |
| DELETE | `/colleges/{id}` | 删除学院 | admin, staff |

---

### 3.4 专业管理 `/api/v1/majors`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/majors` | 专业列表（支持college_id筛选） | admin, staff |
| POST | `/majors` | 创建专业 | admin, staff |
| GET | `/majors/{id}` | 专业详情 | admin, staff |
| PUT | `/majors/{id}` | 更新专业 | admin, staff |
| DELETE | `/majors/{id}` | 删除专业 | admin, staff |

---

### 3.5 教师管理 `/api/v1/teachers`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/teachers` | 教师列表（分页+筛选） | admin, staff |
| POST | `/teachers` | 创建教师 | admin, staff |
| GET | `/teachers/{id}` | 教师详情 | admin, staff |
| PUT | `/teachers/{id}` | 更新教师 | admin, staff |
| DELETE | `/teachers/{id}` | 删除教师 | admin, staff |
| POST | `/teachers/import` | 批量导入教师（Excel） | admin, staff |
| GET | `/teachers/import/template` | 下载导入模板 | admin, staff |
| GET | `/teachers/{id}/courses` | 教师授课列表 | admin, staff, teacher |

---

### 3.6 学生管理 `/api/v1/students`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/students` | 学生列表（分页+筛选） | admin, staff |
| POST | `/students` | 创建学生 | admin, staff |
| GET | `/students/{id}` | 学生详情 | admin, staff, teacher |
| PUT | `/students/{id}` | 更新学生 | admin, staff |
| DELETE | `/students/{id}` | 删除学生 | admin, staff |
| POST | `/students/import` | 批量导入学生（Excel） | admin, staff |
| GET | `/students/import/template` | 下载导入模板 | admin, staff |

---

### 3.7 班级管理 `/api/v1/classes`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/classes` | 班级列表 | admin, staff, teacher |
| POST | `/classes` | 创建班级 | admin, staff |
| PUT | `/classes/{id}` | 更新班级 | admin, staff |
| DELETE | `/classes/{id}` | 删除班级 | admin, staff |

---

### 3.8 学期管理 `/api/v1/semesters`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/semesters` | 学期列表 | admin, staff |
| POST | `/semesters` | 创建学期 | admin, staff |
| PUT | `/semesters/{id}/current` | 设为当前学期 | admin, staff |

---

### 3.9 课程管理 `/api/v1/courses`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/courses` | 课程列表（筛选：semester/college/teacher） | admin, staff |
| POST | `/courses` | 创建课程 | admin, staff |
| GET | `/courses/{id}` | 课程详情 | admin, staff, teacher |
| PUT | `/courses/{id}` | 更新课程 | admin, staff |
| DELETE | `/courses/{id}` | 删除课程 | admin, staff |

---

### 3.10 教室管理 `/api/v1/classrooms`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/classrooms` | 教室列表 | admin, staff |
| POST | `/classrooms` | 创建教室 | admin, staff |
| GET | `/classrooms/{id}` | 教室详情 | admin, staff |
| PUT | `/classrooms/{id}` | 更新教室 | admin, staff |
| DELETE | `/classrooms/{id}` | 删除教室 | admin, staff |

---

### 3.11 排课管理 `/api/v1/schedules`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/schedules` | 排课列表（筛选：semester/teacher/classroom） | admin, staff |
| POST | `/schedules/generate` | 触发自动排课（异步） | admin, staff |
| GET | `/schedules/task/{task_id}/status` | 查询排课任务进度 | admin, staff |
| POST | `/schedules` | 手动添加排课（含冲突检测） | admin, staff |
| PUT | `/schedules/{id}` | 手动调整排课 | admin, staff |
| DELETE | `/schedules/{id}` | 删除排课记录 | admin, staff |

#### POST `/schedules/generate`
**Request**:
```json
{
  "semester_id": 1,
  "course_ids": [1, 2, 3, 4, 5]
}
```
**Response**:
```json
{
  "code": 202,
  "message": "排课任务已提交",
  "data": {
    "task_id": "abc-123-def"
  }
}
```

---

### 3.12 选课管理 `/api/v1/selections`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/selections/available` | 学生可选课程列表 | student |
| POST | `/selections/enroll` | 选课（高并发处理） | student |
| POST | `/selections/drop` | 退课 | student |
| GET | `/selections/my` | 我的已选课程 | student |
| GET | `/selections/stats` | 选课统计 | admin, staff |

#### POST `/selections/enroll`
**Request**:
```json
{
  "course_id": 10
}
```
**Response（成功）**:
```json
{
  "code": 200,
  "message": "选课成功",
  "data": null
}
```
**Response（容量已满）**:
```json
{
  "code": 400,
  "message": "课程名额已满",
  "data": null
}
```
**Response（冲突）**:
```json
{
  "code": 409,
  "message": "名额已满，请刷新重试",
  "data": null
}
```

---

### 3.13 课表系统 `/api/v1/timetable`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/timetable/teacher` | 教师本周课表 | teacher |
| GET | `/timetable/student` | 学生本周课表 | student |
| GET | `/timetable/query` | 全局课表查询（class/teacher/classroom） | admin, staff |

#### GET `/timetable/teacher?week=3`
**Response**:
```json
{
  "code": 200,
  "data": [
    {
      "day_of_week": 1,
      "period_start": 1,
      "period_end": 2,
      "course_name": "高等数学",
      "classroom": "A301",
      "class_name": "计算机2401班"
    }
  ]
}
```

---

### 3.14 点名系统 `/api/v1/attendances`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/attendances/students` | 获取点名学生列表（按课程+日期） | teacher |
| POST | `/attendances/mark` | 标记出勤 | teacher |
| GET | `/attendances/records` | 出勤记录查询 | admin, staff, teacher |
| GET | `/attendances/my` | 我的出勤记录 | student |

#### POST `/attendances/mark`
**Request**:
```json
{
  "course_id": 5,
  "date": "2026-03-15",
  "records": [
    {"student_id": 1, "status": "present"},
    {"student_id": 2, "status": "late"},
    {"student_id": 3, "status": "absent"}
  ]
}
```

---

### 3.15 考勤统计 `/api/v1/attendance-stats`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/attendance-stats/course/{course_id}` | 课程出勤率 | admin, staff, teacher |
| GET | `/attendance-stats/student/{student_id}` | 学生出勤率 | admin, staff, teacher, student(本人) |
| GET | `/attendance-stats/overview` | 出勤概览 | admin, staff |

---

### 3.16 成绩管理 `/api/v1/scores`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/scores/course/{course_id}/students` | 课程学生成绩列表 | teacher |
| POST | `/scores/batch` | 批量录入/更新成绩 | teacher |
| PUT | `/scores/course/{course_id}/publish` | 发布成绩 | teacher |
| GET | `/scores/my` | 我的成绩 | student |
| GET | `/scores/logs/{score_id}` | 成绩修改日志 | admin, staff |

#### POST `/scores/batch`
**Request**:
```json
{
  "course_id": 5,
  "scores": [
    {"student_id": 1, "score": 85.5},
    {"student_id": 2, "score": 92.0},
    {"student_id": 3, "score": 60.0}
  ]
}
```

---

### 3.17 作业管理 `/api/v1/assignments`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/assignments` | 作业列表（按课程） | admin, staff, teacher, student |
| POST | `/assignments` | 发布作业 | teacher |
| GET | `/assignments/{id}` | 作业详情 | 登录用户 |
| DELETE | `/assignments/{id}` | 删除作业 | teacher |
| GET | `/assignments/{id}/submissions` | 学生提交列表 | teacher |
| POST | `/assignments/{id}/submit` | 提交作业 | student |
| PUT | `/assignments/submissions/{id}/review` | 批阅作业 | teacher |

---

### 3.18 请假审批 `/api/v1/leaves`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| POST | `/leaves` | 提交请假申请 | student |
| GET | `/leaves/pending` | 待审批列表 | teacher, staff |
| GET | `/leaves/my` | 我的申请列表 | student |
| PUT | `/leaves/{id}/teacher-review` | 教师审批 | teacher |
| PUT | `/leaves/{id}/staff-review` | 教务员审批 | staff |

---

### 3.19 学业预警 `/api/v1/alerts`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/alerts` | 预警列表 | admin, staff |
| POST | `/alerts/generate` | 手动生成预警（也可定时自动） | admin, staff |
| PUT | `/alerts/{id}/handle` | 处理预警 | staff |

---

### 3.20 社团管理 `/api/v1/clubs`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/clubs` | 社团列表 | admin, staff |
| POST | `/clubs` | 创建社团 | admin, staff |
| PUT | `/clubs/{id}` | 更新社团 | admin, staff |
| DELETE | `/clubs/{id}` | 删除社团 | admin, staff |
| POST | `/clubs/{id}/members` | 添加成员 | admin, staff |
| DELETE | `/clubs/{id}/members/{student_id}` | 移除成员 | admin, staff |
| GET | `/clubs/{id}/members` | 成员列表 | admin, staff |

---

### 3.21 通知公告 `/api/v1/notices`

| 方法 | 路径 | 描述 | 权限 |
| :--- | :--- | :--- | :--- |
| GET | `/notices` | 公告列表（按角色过滤） | 登录用户 |
| POST | `/notices` | 发布公告 | admin, staff |
| PUT | `/notices/{id}` | 更新公告 | admin, staff |
| DELETE | `/notices/{id}` | 删除公告 | admin, staff |
| PUT | `/notices/{id}/publish` | 发布/撤回公告 | admin, staff |

---

## 4. 错误码规范

| code | 说明 |
| :--- | :--- |
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证（Token过期/无效） |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 409 | 数据冲突（乐观锁/选课冲突） |
| 422 | 数据校验失败 |
| 429 | 请求过于频繁（限流） |
| 500 | 服务器内部错误 |
