# 教务管理系统

企业级教务管理系统，基于 FastAPI + Vue3 + MySQL 构建。

## 技术栈

| 层级 | 技术 |
| :--- | :--- |
| 后端框架 | Python 3.13 + FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| 数据库 | MySQL 8.0 |
| 缓存/队列 | Redis 7 |
| 异步任务 | Celery |
| 前端 | Vue 3.5 + Element Plus 2.9 |
| 构建 | Vite 6 |

## 快速启动

### 后端

```bash
conda activate demo2
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```
├── backend/          # FastAPI后端
│   ├── app/
│   │   ├── model/    # ORM模型
│   │   ├── dto/      # Pydantic Schema
│   │   ├── router/   # 路由层
│   │   ├── service/  # 业务层
│   │   ├── dao/      # 数据访问层
│   │   ├── common/   # 通用模块
│   │   ├── utils/    # 工具模块
│   │   └── tasks/    # Celery任务
│   └── requirements.txt
├── frontend/         # Vue3前端
│   └── src/
│       ├── router/   # 路由配置
│       ├── store/    # Pinia状态
│       ├── api/      # 接口调用
│       └── views/    # 页面组件
├── docs/             # 设计文档
└── tests/            # 测试
```

## 文档索引

| 文档 | 路径 |
| :--- | :--- |
| PRD总索引 | [docs/prd/README.md](docs/prd/README.md) |
| 架构设计 | [docs/architecture/architecture-design.md](docs/architecture/architecture-design.md) |
| 数据库设计 | [docs/architecture/database.md](docs/architecture/database.md) |
| API接口设计 | [docs/api/api-design.md](docs/api/api-design.md) |
| 部署说明 | [docs/architecture/deployment.md](docs/architecture/deployment.md) |

## 版本

| 版本 | 日期 | 说明 |
| :--- | :--- | :--- |
| v1.0-dev | 2026-07-22 | 设计阶段，PRD+架构文档完成 |
