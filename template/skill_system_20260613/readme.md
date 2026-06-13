# Skill System 20260613 Template

基于 `planer_feishu_20260412` 增强，新增**可插拔 Skill 系统**。

## 模板血缘

```
default → default_20260406 → planer_20260408 → planer_feishu_20260412 → skill_system_20260613  ← 当前
```

## 核心新增功能

### 可插拔 Skill 系统

Agent 能力以 Skill（技能包）形式管理：

| 特性 | 说明 |
|------|------|
| **内置 Skill** | `skills/` 目录，模板自带 |
| **工作区 Skill** | `workspace/{agent_id}/skills/`，Agent 可自行创建 |
| **渐进式加载** | 默认只加载技能索引，Agent 按需读取完整内容 |
| **SKILL.md 格式** | Markdown + YAML frontmatter，描述技能规范 |

### 内置 Skill

| Skill | 说明 |
|-------|------|
| `patent-writer` | 专利撰写流程与规范 |
| `code-reviewer` | 代码审查标准与流程 |

## 继承特性

### Plan 任务计划（来自 planer）
`create_plan` · `add_task_to_plan` · `get_plan_status` · `update_task_progress` · `execute_next_plan_task`

### 飞书机器人（来自 planer_feishu）
消息接入与自动回复。

### 原子化编辑工具（来自 default_20260406）
`replace_string_in_file` · `append_to_file` · `read_file_range` · `tail_file` · `grep_file`

## 完整工具集（16 个）

基础工具（6）+ Plan 工具（5）+ 原子化编辑工具（5）

## Skill 注入机制

Skill 通过**上下文注入**（system prompt）引入，无需独立 Tool。Agent 启动时自动在 system prompt 中看到所有可用 Skill 的摘要列表（名称、描述、可用性）。

### 注入模式配置

```env
# Plan 注入（默认 dynamic）
PLAN_INJECTION_MODE=dynamic  # 每轮 LLM 调用重新查询 plan 状态
PLAN_INJECTION_MODE=static   # 对话开始时计算一次

# Skill 注入（默认 static）
SKILLS_INJECTION_MODE=static   # 启动时计算一次
SKILLS_INJECTION_MODE=dynamic   # 每轮 LLM 调用重新扫描 skills/ 目录
```

| 模式 | 优点 | 缺点 |
|------|------|------|
| `static` | token 开销稳定，无文件 IO | Agent 新增/修改后需重启生效 |
| `dynamic` | 实时反映最新状态 | 每轮额外文件扫描/查询开销 |

**说明**：Plan 推荐 `dynamic`（任务状态在对话中频繁变化）；Skill 推荐 `static`（内容通常稳定）。

## 替换范围配置

由 `.template` 文件定义：
- `replace`：替换 `app/`、`run.py`、`requirements.txt`
- `exclude`：替换时排除的目录/文件

## 目录结构

```
skill_system_20260613/
├── app/                  # FastAPI 应用（含 Agent Core、Plan、Feishu）
├── skills/               # 内置 Skill（SKILL.md 格式）
├── readme.md
├── requirements.txt
├── run.py
└── .template             # 模板元信息
```
