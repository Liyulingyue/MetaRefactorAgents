# MCP Tools 20260613 Template

基于 `skill_system_20260613` 增强，新增 **MCP 集成**与 **ToolRegistry 可插拔架构**。

## 模板血缘

```
default → default_20260406 → planer_20260408 → planer_feishu_20260412
→ skill_system_20260613 → mcp_tools_20260613  ← 当前
```

## 核心新增功能

### ToolRegistry 可插拔架构 ✅
将工具从 if-elif 链迁移到注册表模式，支持运行时注册/注销工具。

| 文件 | 说明 |
|------|------|
| `app/core/registry.py` | `Tool` 基类 + `ToolRegistry` 单例 |
| `app/core/tools.py` | 内置工具注册 + `handle_tool_call` 委托 |

注册表接口：
- `get_tool_registry()` — 获取全局单例
- `register_tool(tool)` — 运行时注册新工具
- `unregister_tool(name)` — 运行时注销工具

### MCP 集成（TODO）
支持连接 MCP 服务器，将外部工具接入 Agent 工具集。

## 继承特性

### Plan 任务计划（来自 planer）
`create_plan` · `add_task_to_plan` · `get_plan_status` · `update_task_progress` · `execute_next_plan_task`

### 飞书机器人（来自 planer_feishu）
消息接入与自动回复。

### 原子化编辑工具（来自 default_20260406）
`replace_string_in_file` · `append_to_file` · `read_file_range` · `tail_file` · `grep_file`

### Skill 系统（来自 skill_system）
内置 Skill：patent-writer · code-reviewer

## 完整工具集（16 个）

基础工具（6）+ Plan 工具（5）+ 原子化编辑工具（5）

## 注入模式配置

```env
PLAN_INJECTION_MODE=dynamic   # 每轮 LLM 调用重新查询 plan 状态
SKILLS_INJECTION_MODE=static  # 启动时计算一次
```

## 替换范围配置

由 `.template` 文件定义：
- `replace`：替换 `app/`、`run.py`、`requirements.txt`
- `exclude`：替换时排除的目录/文件

## 目录结构

```
mcp_tools_20260613/
├── app/
│   └── core/
│       ├── registry.py    # ToolRegistry + Tool 基类
│       ├── tools.py      # 内置工具（已迁移到 registry）
│       ├── plan.py       # Plan Service
│       ├── skills.py     # Skills Loader
│       ├── feishu.py     # Feishu Client
│       └── config.py     # 配置
├── skills/               # 内置 Skill（SKILL.md 格式）
├── readme.md
├── requirements.txt
├── run.py
└── .template             # 模板元信息
```
