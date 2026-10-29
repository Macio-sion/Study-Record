# Agent的invoke模式服务发布

`pip install "redis-agent-kit[all]"`

## 编程范式

### 工程流程
- 实现Task
    - 把agent、llm的调用封装成Task
    - 把Task作为Web服务发布
- 启动服务
    - 启动Web服务
    - 启动Task
- 客户端调用
    - 本地python调用Web服务
    - 前端调用Web服务
