# Conversation 20260613 Template

基于 `mcp_tools_20260613` 增强，新增**对话上下文压缩与总结策略**。

## 模板血缘

```
default → default_20260406 → planer_20260408 → planer_feishu_20260412
→ skill_system_20260613 → mcp_tools_20260613 → conversation_20260613  ← 当前
```

## 核心新增功能

### 对话上下文压缩与总结策略（TODO）

解决长对话上下文无限膨胀导致的 token 爆炸和 context 溢出问题。

## 继承特性

### MCP 集成（来自 mcp_tools）
HTTP/SSE + stdio 双传输，支持热插拔工具。

### ToolRegistry 可插拔架构（来自 mcp_tools）
内置工具注册到全局注册表，支持运行时注册/注销。

### Plan 任务计划（来自 planer）
`create_plan` · `add_task_to_plan` · `get_plan_status` · `update_task_progress` · `execute_next_plan_task`

### 飞书机器人（来自 planer_feishu）
消息接入与自动回复。

### 原子化编辑工具（来自 default_20260406）
`replace_string_in_file` · `append_to_file` · `read_file_range` · `tail_file` · `grep_file`

### Skill 系统（来自 skill_system）
内置 Skill：patent-writer · code-reviewer

## 注入模式配置

```env
PLAN_INJECTION_MODE=dynamic
SKILLS_INJECTION_MODE=static
MCP_INJECTION_MODE=static
```

## 目录结构

```
conversation_20260613/
├── app/
│   └── core/
│       ├── agent.py        # 对话压缩逻辑
│       ├── autocompact.py # 上下文压缩模块（TODO）
│       ├── registry.py
│       ├── tools.py
│       ├── plan.py
│       ├── skills.py
│       ├── mcp_client.py
│       └── config.py
├── skills/
├── readme.md
├── requirements.txt
├── run.py
└── .template
```
