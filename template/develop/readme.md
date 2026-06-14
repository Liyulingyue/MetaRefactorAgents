# Develop Template

开发分支，基于 `feishu_memory_20260613`。

## 模板血缘

```
default → default_20260406 → planer_20260408 → planer_feishu_20260412
→ skill_system_20260613 → mcp_tools_20260613 → conversation_20260613
→ feishu_memory_20260613 → develop  ← 当前
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

### 两层记忆架构

- **会话层**：sessions/*.ndjson，按 chat_id 存储，包含压缩摘要
- **长期层**：MEMORY.md，Agent 重要事实持久化

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
```

## 目录结构

```
develop/
├── app/
│   └── core/
│       ├── agent.py        # Agent 核心，含 system/memory 注入
│       ├── autocompact.py  # 对话压缩模块
│       ├── config.py       # 配置管理
│       ├── feishu.py       # 飞书 WS + ChatWorker
│       ├── memory.py       # 长期记忆加载
│       ├── mcp_client.py
│       ├── plan.py
│       ├── registry.py
│       ├── session.py      # 会话管理，NDJSON 存储
│       ├── skills.py
│       └── tools.py
├── skills/                 # 内置 Skill
├── sessions/               # 会话文件存储（运行后生成）
├── SYSTEM.md              # Agent 身份
├── MEMORY.md              # 长期记忆
├── readme.md
├── requirements.txt
├── run.py
└── .template
```
