# Planer 20260408 Template

基于 `default_20260406` 增强，新增 **Plan 任务计划编排**功能。

## 模板血缘

```
default → default_20260406 → planer_20260408  ← 当前
```

## 核心新增功能

### Plan 任务计划

Agent 可通过 Tool 调用自主创建和管理任务计划序列：

| Tool | 功能 |
|------|------|
| `create_plan` | 创建新计划，支持初始化任务列表 |
| `add_task_to_plan` | 向现有计划添加任务 |
| `get_plan_status` | 查看计划状态和任务详情 |
| `update_task_progress` | 更新任务状态（pending/running/completed/failed） |
| `execute_next_plan_task` | 获取并执行下一个待办任务 |

**数据存储**：`plans/` 目录（JSON 格式持久化）

### Agent 自主工作流

```
1. create_plan(name="专利撰写", tasks=[...])
2. execute_next_plan_task(plan_id)  → 获取任务详情
3. [执行任务逻辑]
4. update_task_progress(plan_id, task_id, "completed", result={...})
5. 重复步骤 2-4 直到所有任务完成
```

### 任务状态流转

```
pending → running → completed
                    ↘ failed
```

## REST API

```
GET    /api/v1/plans/                              - 列出所有计划
POST   /api/v1/plans/                              - 创建计划
GET    /api/v1/plans/{plan_id}                     - 获取计划详情
DELETE /api/v1/plans/{plan_id}                     - 删除计划
POST   /api/v1/plans/{plan_id}/tasks               - 添加任务
PATCH  /api/v1/plans/{plan_id}/tasks/{task_id}/status  - 更新任务状态
POST   /api/v1/plans/{plan_id}/next                - 执行下一个任务
POST   /api/v1/plans/{plan_id}/pause               - 暂停计划
POST   /api/v1/plans/{plan_id}/resume              - 恢复计划
```

## 继承特性

### 原子化编辑工具（来自 default_20260406）
`replace_string_in_file` · `append_to_file` · `read_file_range` · `tail_file` · `grep_file`

### 日志管理（来自 default_20260406）
`thoughts.md` 超过 100KB 自动归档到 `logs/archived/`

## 完整工具集（16 个）

基础工具 + Plan 工具（5）+ 原子化编辑工具（5）

## 替换范围配置

由 `.template` 文件定义：
- `replace`：替换的目录/文件列表
- `exclude`：替换时排除的目录/文件

当前配置：替换 `app/` 和 `run.py`，Agent 的工作文件不受影响。

## 目录结构

```
planer_20260408/
├── app/                  # FastAPI 应用（含 Agent Core、Plan、Tools）
├── readme.md
├── requirements.txt
├── run.py
└── .template             # 模板元信息
```
