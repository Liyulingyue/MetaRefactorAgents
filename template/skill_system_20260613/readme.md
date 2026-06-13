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

基础工具 + Plan 工具（5）+ 原子化编辑工具（5）

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
