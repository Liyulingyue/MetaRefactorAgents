# Planer 20260408 Template

基于 default_20260406 增强，支持 Plan 任务计划编排功能。

## 新增特性

### Plan 功能
Agent 可通过 Tool 调用自主创建和管理任务计划：

| Tool | 功能 |
|------|------|
| `create_plan` | 创建新计划，支持初始化任务列表 |
| `add_task_to_plan` | 向现有计划添加任务 |
| `get_plan_status` | 查看计划状态和任务详情 |
| `update_task_progress` | 更新任务状态 (pending/running/completed/failed) |
| `execute_next_plan_task` | 获取并执行下一个待办任务 |

**数据存储：** `plans/` 目录（JSON 格式持久化）

### Agent 自主工作流

```
1. create_plan(name="ResNet报告", tasks=[...])
2. execute_next_plan_task(plan_id)  → 获取任务详情
3. [执行任务逻辑]
4. update_task_progress(plan_id, task_id, "completed", result={...})
5. 重复步骤 2-4 直到所有任务完成
```

### 原子化编辑工具
- `replace_string_in_file`：精确替换文件内容
- `append_to_file`：追加内容到文件
- `read_file_range`：读取文件指定行范围
- `tail_file`：读取文件末尾 N 行
- `grep_file`：在文件中搜索文本

### 日志管理
- `thoughts.md` 超过 100KB 自动归档到 `logs/archived/`
- 工具调用异常写入 `logs/error.log`

## Plan Tool 详细说明

### create_plan
```json
{
  "name": "ResNet报告",
  "description": "撰写ResNet深度学习报告",
  "tasks": [
    {
      "name": "搜索ResNet资料",
      "action": "grep_file",
      "params": {"file_path": ".", "pattern": "ResNet"}
    },
    {
      "name": "生成报告草稿",
      "action": "write_file",
      "params": {"file_path": "report.md", "content": "# ResNet报告\n..."}
    }
  ]
}
```

### 任务状态流转
```
pending → running → completed
                    ↘ failed
```

## REST API

Plan 功能也提供外部 REST API 接口：

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

## 替换范围配置

由 `.template` 文件定义（JSON 格式）：
- `replace`：要替换的目录/文件列表
- `exclude`：替换时要排除的目录/文件

当前配置：替换 `app/` 和 `run.py`，Agent 的工作文件不受影响。
