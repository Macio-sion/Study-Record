# 数据库设计详细说明

## 1. 概述

本系统使用 MySQL 8.0 作为关系型数据库，字符集 utf8mb4，排序规则 utf8mb4_unicode_ci。

数据库名称：`edu_management`

## 2. 表清单（26张）

| 序号 | 表名 | 说明 | 优先级 |
| :--- | :--- | :--- | :---: |
| 1 | users | 系统用户表（认证+角色） | P0 |
| 2 | colleges | 学院表 | P0 |
| 3 | majors | 专业表 | P0 |
| 4 | classes | 班级表 | P0 |
| 5 | teachers | 教师表 | P0 |
| 6 | students | 学生表 | P0 |
| 7 | semesters | 学期表 | P0 |
| 8 | courses | 课程表（含乐观锁version） | P0 |
| 9 | classrooms | 教室表 | P0 |
| 10 | schedules | 排课结果表 | P0 |
| 11 | course_selections | 选课记录表 | P0 |
| 12 | attendances | 出勤记录表 | P0 |
| 13 | scores | 成绩表 | P0 |
| 14 | score_logs | 成绩修改日志表 | P0 |
| 15 | assignments | 作业表 | P0 |
| 16 | assignment_submissions | 作业提交表 | P0 |
| 17 | leave_requests | 请假申请表 | P1 |
| 18 | alert_records | 学业预警记录表 | P1 |
| 19 | clubs | 社团表 | P1 |
| 20 | club_members | 社团成员表 | P1 |
| 21 | notices | 通知公告表 | P1 |
| 22 | roles | 角色定义表 | P0 |
| 23 | permissions | 权限表 | P0 |
| 24 | role_permissions | 角色-权限关联表 | P0 |
| 25 | user_logs | 操作日志表 | P2 |
| 26 | import_records | 批量导入记录表 | P0 |

## 3. DDL脚本（关键表）

### users
```sql
CREATE TABLE `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL COMMENT '用户名',
  `password_hash` VARCHAR(255) NOT NULL COMMENT 'bcrypt密码',
  `role_code` VARCHAR(20) NOT NULL COMMENT '角色编码',
  `real_name` VARCHAR(50) NOT NULL COMMENT '真实姓名',
  `phone` VARCHAR(20) DEFAULT NULL COMMENT '手机号',
  `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  KEY `idx_role_code` (`role_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统用户表';
```

### courses
```sql
CREATE TABLE `courses` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(20) NOT NULL COMMENT '课程编码',
  `name` VARCHAR(200) NOT NULL COMMENT '课程名称',
  `semester_id` INT NOT NULL COMMENT '学期ID',
  `college_id` INT NOT NULL COMMENT '开课学院ID',
  `teacher_id` INT NOT NULL COMMENT '授课教师ID',
  `credit` DECIMAL(3,1) NOT NULL COMMENT '学分',
  `max_capacity` INT NOT NULL COMMENT '最大容量',
  `selected_count` INT NOT NULL DEFAULT 0 COMMENT '已选人数',
  `hours` INT NOT NULL COMMENT '总学时',
  `type` VARCHAR(20) NOT NULL COMMENT '必修/选修',
  `description` VARCHAR(500) DEFAULT NULL,
  `version` INT NOT NULL DEFAULT 1 COMMENT '乐观锁版本号',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_semester` (`semester_id`),
  KEY `idx_teacher` (`teacher_id`),
  KEY `idx_college` (`college_id`),
  CONSTRAINT `fk_course_semester` FOREIGN KEY (`semester_id`) REFERENCES `semesters` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_course_college` FOREIGN KEY (`college_id`) REFERENCES `colleges` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_course_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程表';
```

### schedules
```sql
CREATE TABLE `schedules` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `course_id` INT NOT NULL COMMENT '课程ID',
  `classroom_id` INT NOT NULL COMMENT '教室ID',
  `teacher_id` INT NOT NULL COMMENT '教师ID',
  `semester_id` INT NOT NULL COMMENT '学期ID',
  `week_start` INT NOT NULL COMMENT '起始周次',
  `week_end` INT NOT NULL COMMENT '结束周次',
  `day_of_week` INT NOT NULL COMMENT '星期(1-7)',
  `period_start` INT NOT NULL COMMENT '起始节次',
  `period_end` INT NOT NULL COMMENT '结束节次',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_slot` (`classroom_id`, `semester_id`, `week_start`, `day_of_week`, `period_start`) COMMENT '教室冲突检测',
  KEY `idx_teacher_week` (`teacher_id`, `semester_id`, `week_start`) COMMENT '教师课表查询',
  KEY `idx_course` (`course_id`),
  KEY `idx_semester_day` (`semester_id`, `day_of_week`) COMMENT '班级课表查询',
  CONSTRAINT `fk_schedule_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_schedule_classroom` FOREIGN KEY (`classroom_id`) REFERENCES `classrooms` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_schedule_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_schedule_semester` FOREIGN KEY (`semester_id`) REFERENCES `semesters` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='排课结果表';
```

### course_selections
```sql
CREATE TABLE `course_selections` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `student_id` INT NOT NULL COMMENT '学生ID',
  `course_id` INT NOT NULL COMMENT '课程ID',
  `semester_id` INT NOT NULL COMMENT '学期ID',
  `selected_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '选课时间',
  `status` VARCHAR(10) NOT NULL DEFAULT 'selected' COMMENT 'selected/dropped',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_student_course` (`student_id`, `course_id`, `semester_id`) COMMENT '防重复选课',
  KEY `idx_student` (`student_id`, `semester_id`) COMMENT '学生课表查询',
  KEY `idx_course` (`course_id`) COMMENT '选课统计',
  CONSTRAINT `fk_selection_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_selection_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_selection_semester` FOREIGN KEY (`semester_id`) REFERENCES `semesters` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='选课记录表';
```

### attendances
```sql
CREATE TABLE `attendances` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `course_id` INT NOT NULL COMMENT '课程ID',
  `student_id` INT NOT NULL COMMENT '学生ID',
  `teacher_id` INT NOT NULL COMMENT '点名教师ID',
  `date` DATE NOT NULL COMMENT '上课日期',
  `status` VARCHAR(20) NOT NULL COMMENT 'present/late/early_leave/absent',
  `remark` VARCHAR(200) DEFAULT NULL COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_course_student_date` (`course_id`, `student_id`, `date`) COMMENT '防重复点名',
  KEY `idx_student` (`student_id`) COMMENT '学生出勤查询',
  CONSTRAINT `fk_attendance_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_attendance_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_attendance_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='出勤记录表';
```

## 4. 事务管理策略

| 场景 | 事务范围 | 隔离级别 |
| :--- | :--- | :--- |
| 创建教师 | users + teachers | READ COMMITTED |
| 创建学生 | users + students | READ COMMITTED |
| 选课 | courses(乐观锁) + course_selections | READ COMMITTED |
| 批量成绩录入 | scores批量INSERT/UPDATE | READ COMMITTED |
| 排课结果保存 | schedules批量INSERT | READ COMMITTED |
