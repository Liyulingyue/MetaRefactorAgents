# Cron Template

基于 `feishu_memory_20260613`，新增 Cron 定时任务功能。

## 模板血缘

```
default → default_20260406 → planer_20260408 → planer_feishu_20260412
→ skill_system_20260613 → mcp_tools_20260613 → conversation_20260613
→ feishu_memory_20260613 → cron_20260614  ← 当前
```

## 核心功能

### 飞书多轮对话

按 `chat_id` 维护独立会话上下文，支持消息队列与命令：

- `/new` - 开启新对话，清空上下文
- `/stop` - 停止当前处理任务

### 对话上下文压缩

基于 token 数量自动压缩，当 history 超过阈值时触发压缩，将早期消息摘要化。

### 长期记忆

- `SYSTEM.md` - Agent 身份定义，支持模型自修改
- `MEMORY.md` - 全局长期记忆，动态注入 system prompt

### 思考标签隐藏（HIDE_THINK_TAGS）

模型 responses 中的 `<think>...</think>` 思考标签默认保留，可通过配置 `HIDE_THINK_TAGS=true` 启用过滤，将思考过程从响应中移除后再返回给用户。

### 两层记忆架构

- **会话层**：sessions/*.ndjson，按 chat_id 存储，包含压缩摘要
- **长期层**：MEMORY.md，Agent 重要事实持久化

### Cron 定时任务

支持三种调度类型：

- `at` - 一次性任务（指定时间戳）
- `every` - 间隔任务（指定毫秒）
- `cron` - 标准 Cron 表达式（如 `0 9 * * *`）

**触发行为：**

- `message` - Agent 的 prompt，Agent 会自动调用所需 tools 完成智能任务
- `session_key` - 飞书 chat_id，结果发送目标

**使用方式：**
```
创建定时任务 → Agent.run(message) → 结果发送到 session_key
```

**特性：**
- 持久化到 `cron/jobs.json`，重启后自动恢复
- 使用 FileLock + fsync 保证并发安全
- 支持手动触发、启用/禁用、删除
- 最大休眠 5 分钟避免空转

## 配置项

```env
# 飞书
FEISHU_APP_ID=xxx
FEISHU_APP_SECRET=xxx

# 会话
SESSION_STORAGE_PATH=./sessions
SESSION_FILE_MAX_SIZE=102400  # 100KB 自动归档

# 上下文压缩
HISTORY_SUMMARY_THRESHOLD=25000  # token 阈值

# 长期记忆
MEMORY_FILE_PATH=MEMORY.md
MEMORY_INJECTION_MODE=dynamic

# 系统提示
SYSTEM_FILE_PATH=SYSTEM.md
SYSTEM_INJECTION_MODE=dynamic

# Cron 定时任务
CRON_STORAGE_PATH=./cron
CRON_ENABLED=true

# 思考标签隐藏
HIDE_THINK_TAGS=false  # true 启用后过滤掉模型的 <think>...</think> 标签
```

## API 端点

```
GET    /api/v1/cron/              # 列出所有定时任务
POST   /api/v1/cron/              # 创建定时任务
GET    /api/v1/cron/{job_id}      # 获取任务详情
PATCH  /api/v1/cron/{job_id}      # 更新任务
DELETE /api/v1/cron/{job_id}      # 删除任务
POST   /api/v1/cron/{job_id}/enable   # 启用
POST   /api/v1/cron/{job_id}/disable  # 禁用
POST   /api/v1/cron/{job_id}/run      # 手动触发
GET    /api/v1/cron/status         # 服务状态
```

## Agent Tools

- `create_cron` / `list_crons` / `delete_cron` / `enable_cron` / `disable_cron`

## 目录结构

```
cron_20260614/
├── app/
│   ├── core/
│   │   ├── agent.py        # Agent 核心，含 system/memory 注入
│   │   ├── autocompact.py  # 对话压缩模块
│   │   ├── config.py       # 配置管理
│   │   ├── cron_service.py # Cron 定时任务服务
│   │   ├── cron_types.py   # Cron 类型定义
│   │   ├── feishu.py       # 飞书 WS + ChatWorker
│   │   ├── memory.py       # 长期记忆加载
│   │   ├── mcp_client.py
│   │   ├── plan.py
│   │   ├── registry.py
│   │   ├── session.py      # 会话管理，NDJSON 存储
│   │   ├── skills.py
│   │   └── tools.py
│   └── routers/
│       ├── agent.py
│       ├── cron.py         # Cron REST API
│       ├── feishu.py
│       ├── files.py
│       ├── health.py
│       └── plan.py
├── skills/                 # 内置 Skill
├── sessions/               # 会话文件存储（运行后生成）
├── cron/                   # Cron 任务存储（运行后生成）
├── SYSTEM.md              # Agent 身份
├── MEMORY.md              # 长期记忆
├── readme.md
├── requirements.txt
├── run.py
└── .template
```
