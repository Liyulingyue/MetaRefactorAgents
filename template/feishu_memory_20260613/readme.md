# Feishu Memory 20260613 Template

基于 `conversation_20260613` 增强，新增**飞书多轮对话**与**长期记忆**策略。

## 模板血缘

```
default → default_20260406 → planer_20260408 → planer_feishu_20260412
→ skill_system_20260613 → mcp_tools_20260613 → conversation_20260613
→ feishu_memory_20260613  ← 当前
```

## 核心新增功能

### 飞书多轮对话

按 `chat_id` 维护独立会话上下文，支持消息队列与命令：

- `/new` - 开启新对话，清空上下文
- `/stop` - 停止当前处理任务

ChatWorker 架构：per-chat-id 独立线程处理，消息队列缓冲。

### 对话上下文压缩（摘要持久化）

基于 token 数量自动压缩，当 history 超过阈值时触发压缩，将早期消息摘要化。

**与上个版本（conversation_20260613）的区别：**

上个版本的压缩是**半成品**：
- 压缩逻辑存在，但摘要（last_summary）只存在于内存
- 每轮对话结束后摘要丢失，无法叠加
- 每次都是从压缩后的 messages 重新开始

当前版本修复了这个问题：
- `on_compact` 回调将摘要存储到 session NDJSON
- 摘要持久化，下轮对话可继续叠加
- 实现真正的**无限上下文**能力

### 长期记忆

- `SYSTEM.md` - Agent 身份定义，支持模型自修改（动态读取）
- `MEMORY.md` - 全局长期记忆，动态注入 system prompt

### 两层记忆架构

- **会话层**：`sessions/*.ndjson`，按 chat_id 存储，包含压缩摘要
- **长期层**：`MEMORY.md`，Agent 重要事实持久化

## 继承特性

### MCP 集成（来自 mcp_tools）
HTTP/SSE + stdio 双传输，支持热插拔工具。

### ToolRegistry 可插拔架构（来自 mcp_tools）
内置工具注册到全局注册表，支持运行时注册/注销。

### Plan 任务计划（来自 planer）
`create_plan` · `add_task_to_plan` · `get_plan_status` · `update_task_progress` · `execute_next_plan_task`

### 原子化编辑工具（来自 default_20260406）
`replace_string_in_file` · `append_to_file` · `read_file_range` · `tail_file` · `grep_file`

### Skill 系统（来自 skill_system）
内置 Skill：patent-writer · code-reviewer

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

## 注入模式配置

```env
PLAN_INJECTION_MODE=dynamic
SKILLS_INJECTION_MODE=static
MCP_INJECTION_MODE=static
MEMORY_INJECTION_MODE=dynamic
SYSTEM_INJECTION_MODE=dynamic
```

## 目录结构

```
feishu_memory_20260613/
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
├── sessions/              # 会话文件存储（运行后生成）
├── SYSTEM.md             # Agent 身份
├── MEMORY.md             # 长期记忆
├── readme.md
├── requirements.txt
├── run.py
└── .template
```
