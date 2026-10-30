-- ============================================================================
-- 简历智能体 · PostgreSQL 表结构设计
-- 持久化策略：核心业务数据落 PostgreSQL；任务队列/会话记忆落 Redis（不在本文件）。
-- 表：users / resumes / resume_versions / job_records / feedback / task_logs
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. 用户表（F-USER-001 账户管理）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            VARCHAR(64)  PRIMARY KEY,                     -- 用户 ID（usr_xxx）
    account       VARCHAR(128) NOT NULL UNIQUE,                 -- 登录账号（手机号/邮箱/用户名）
    password_hash VARCHAR(255) NOT NULL,                        -- PBKDF2 密码散列（salt$hash）
    nickname      VARCHAR(128) DEFAULT '',                      -- 昵称
    avatar        VARCHAR(512) DEFAULT '',                      -- 头像 URL
    phone         VARCHAR(32)  DEFAULT '',                      -- 手机号
    email         VARCHAR(128) DEFAULT '',                      -- 邮箱
    job_intention VARCHAR(255) DEFAULT '',                      -- 求职意向
    created_at    TIMESTAMPTZ  DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 2. 简历表（解析引擎产出的 StructuredResume 主数据）
--    fields 即 StructuredResume.fields（value + confidence），pending 为待确认清单。
--    解析引擎唯一产出，供问答/优化两模块复用（唯一数据源）。
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resumes (
    id          VARCHAR(64)  PRIMARY KEY,                       -- 简历 ID（rsm_xxx）
    user_id     VARCHAR(64)  NOT NULL,                          -- 所属用户
    name        VARCHAR(255) DEFAULT '',                        -- 简历名（自定义名/源文件名）
    source_type VARCHAR(16)  DEFAULT '',                        -- 真实格式 pdf/docx/doc/png/jpg
    ocr_used    BOOLEAN      DEFAULT FALSE,                     -- 是否走 OCR
    file_hash   VARCHAR(64)  DEFAULT '',                        -- 文件指纹（解析缓存/去重）
    fields      JSONB        DEFAULT '{}'::jsonb,               -- 结构化字段
    pending     JSONB        DEFAULT '[]'::jsonb,               -- 待确认字段清单
    created_at  TIMESTAMPTZ  DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resumes_user ON resumes (user_id);

-- ----------------------------------------------------------------------------
-- 3. 简历版本表（F-USER-002 版本管理；优化应用/回退/对比）
--    与 services/edit_engine/version.py 的 PostgresVersionStore 保持一致：
--    fields 以 JSON 字符串（TEXT）存储，主键为 (resume_id, version)。
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resume_versions (
    resume_id  VARCHAR(64)  NOT NULL,
    version    VARCHAR(16)  NOT NULL,
    fields     TEXT         NOT NULL,                           -- JSON 字符串
    note       TEXT         DEFAULT '',
    created_at TIMESTAMPTZ  DEFAULT NOW(),
    PRIMARY KEY (resume_id, version)
);

CREATE INDEX IF NOT EXISTS idx_resume_versions_resume ON resume_versions (resume_id);

-- ----------------------------------------------------------------------------
-- 4. 求职记录表（F-USER-003 求职记录管理）
--    status 枚举：待投递/已投递/面试中/已录用/已拒绝
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS job_records (
    id         VARCHAR(64)  PRIMARY KEY,                        -- 记录 ID（job_xxx）
    user_id    VARCHAR(64)  NOT NULL,
    company    VARCHAR(128) DEFAULT '',                         -- 公司
    position   VARCHAR(128) DEFAULT '',                         -- 职位
    status     VARCHAR(32)  DEFAULT '待投递',                   -- 求职状态
    date       DATE         DEFAULT NULL,                       -- 投递/面试日期
    note       TEXT         DEFAULT '',
    created_at TIMESTAMPTZ  DEFAULT NOW(),
    updated_at TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_records_user ON job_records (user_id);

-- ----------------------------------------------------------------------------
-- 5. 反馈表（F-USER-005 产品反馈）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
    id         BIGSERIAL    PRIMARY KEY,
    user_id    VARCHAR(64)  NOT NULL,
    content    TEXT         NOT NULL,
    screenshot TEXT         DEFAULT '',                         -- 截图（URL/base64，可选）
    created_at TIMESTAMPTZ  DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 6. 任务日志表（用于使用统计 parse_count/edit_count/qa_count）
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS task_logs (
    id         BIGSERIAL    PRIMARY KEY,
    task_id    VARCHAR(64)  NOT NULL,                           -- Redis 队列任务 ID（ULID）
    user_id    VARCHAR(64)  NOT NULL,
    task_type  VARCHAR(32)  NOT NULL,                           -- parse/coaching/mock_interview/edit.*
    resume_id  VARCHAR(64)  DEFAULT NULL,
    status     VARCHAR(32)  DEFAULT 'queued',
    created_at TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_logs_user ON task_logs (user_id, task_type);
