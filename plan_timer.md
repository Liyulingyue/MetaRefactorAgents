# Plan 与 Timer 功能设计

## 1. 背景

当前 Agent 系统缺乏任务编排和定时执行能力，需要设计一套机制让 Agent 能够：
- 自主制定、执行和追踪任务计划
- 支持定时/周期性任务触发
- 持久化任务状态，支持 Agent 重启后恢复

## 2. 功能层次

```
Plan（做什么）
  │
  ├── 定义任务序列和依赖关系
  ├── 持久化任务状态
  └── 支持暂停/恢复/取消

Timer（什么时候做）
  │
  ├── 定时触发（指定时间）
  ├── 周期触发（间隔执行）
  └── 由 Plan 里的任务调用
```

**优先级：Plan > Timer**

## 3. Plan 功能设计

### 3.1 核心概念

- **Task（任务）**：最小执行单元
- **Plan（计划）**：由多个 Task 组成的有序序列
- **TaskState**：任务状态（pending / running / completed / failed / paused）

### 3.2 Task 结构

```python
class Task:
    id: str              # 唯一标识
    name: str            # 任务名称
    description: str    # 任务描述
    action: str          # 执行动作（对应 Tool）
    params: dict         # 动作参数
    status: str          # pending / running / completed / failed / paused
    result: Any          # 执行结果
    created_at: str     # 创建时间
    updated_at: str     # 更新时间
    depends_on: List[str] # 依赖任务 ID
```

### 3.3 Plan 结构

```python
class Plan:
    id: str              # 唯一标识
    name: str            # 计划名称
    tasks: List[Task]    # 任务列表
    status: str          # active / paused / completed / cancelled
    created_at: str
    current_task_id: str # 当前执行任务
```

### 3.4 持久化

- 存储位置：`workspace/{agent_id}/plans/{plan_id}.json`
- 状态更新：每次任务状态变化时写入
- 索引文件：`workspace/{agent_id}/plans/index.json`

### 3.5 Agent 接口

```python
# 创建计划
POST /api/v1/plans
{
    "name": "专利撰写计划",
    "tasks": [...]
}

# 获取计划列表
GET /api/v1/plans

# 获取计划详情
GET /api/v1/plans/{plan_id}

# 执行下一个任务
POST /api/v1/plans/{plan_id}/next

# 暂停/恢复计划
POST /api/v1/plans/{plan_id}/pause
POST /api/v1/plans/{plan_id}/resume

# 取消计划
DELETE /api/v1/plans/{plan_id}
```

### 3.6 Tool 扩展

```python
@register_tool
def create_plan(name: str, tasks: List[dict]) -> Plan:
    """创建新计划"""
    
@register_tool
def add_task(plan_id: str, task: dict) -> Task:
    """向计划添加任务"""
    
@register_tool
def execute_plan(plan_id: str) -> Plan:
    """执行计划"""
    
@register_tool
def get_plan_status(plan_id: str) -> Plan:
    """获取计划状态"""
```

## 4. Timer 功能设计

### 4.1 核心概念

- **Timer（定时器）**：周期性触发机制
- **Heartbeat（心跳）**：Agent 存活状态上报

### 4.2 Timer 结构

```python
class Timer:
    id: str              # 唯一标识
    name: str            # 定时器名称
    type: str            # interval / cron
    interval: int         # 间隔（秒），type=interval 时使用
    cron: str            # Cron 表达式，type=cron 时使用
    action: str          # 触发的动作（plan_id 或 tool_name）
    action_params: dict  # 动作参数
    enabled: bool        # 是否启用
    last_run: str        # 上次执行时间
    next_run: str        # 下次执行时间
```

### 4.3 持久化

- 存储位置：`workspace/{agent_id}/timers/{timer_id}.json`
- 索引文件：`workspace/{agent_id}/timers/index.json`
- 定时器状态保存在内存中，由独立的 Timer Service 管理

### 4.4 Agent 接口

```python
# 创建定时器
POST /api/v1/timers
{
    "name": "定期健康检查",
    "type": "interval",
    "interval": 3600,
    "action": "execute_plan",
    "action_params": {"plan_id": "health_check"}
}

# 获取定时器列表
GET /api/v1/timers

# 启用/禁用定时器
POST /api/v1/timers/{timer_id}/enable
POST /api/v1/timers/{timer_id}/disable

# 删除定时器
DELETE /api/v1/timers/{timer_id}
```

### 4.5 Timer Service

```python
class TimerService:
    def __init__(self, agent_id: str):
        self.timers: Dict[str, Timer] = {}
        self.running = True
    
    async def start(self):
        """启动定时器服务"""
        
    async def stop(self):
        """停止定时器服务"""
        
    def add_timer(self, timer: Timer):
        """添加定时器"""
        
    def remove_timer(self, timer_id: str):
        """移除定时器"""
        
    async def check_and_fire(self):
        """检查并触发到期的定时器"""
```

### 4.6 Heartbeat

```python
class Heartbeat:
    agent_id: str
    timestamp: str
    status: str           # running / idle / error
    active_plans: List[str]
    active_timers: int
    cpu_usage: float
    memory_usage: float
```

Heartbeat 可选实现，用于：
- 向 Gateway 上报 Agent 存活状态
- 传递基本资源使用情况
- Gateway 可据此展示 Agent 健康度

## 5. 实现顺序

```
Phase 1: Plan 功能
├── Task/Plan 数据结构定义
├── 持久化层（plans 目录）
├── REST API（CRUD 操作）
├── Tool 扩展（create_plan, execute_plan 等）
└── 任务状态机（pending -> running -> completed/failed）

Phase 2: Timer 功能
├── Timer 数据结构定义
├── 持久化层（timers 目录）
├── Timer Service（独立线程/协程）
├── REST API（CRUD 操作）
└── Tool 扩展（create_timer 等）

Phase 3: 增强功能
├── Plan 内置 Timer 支持（plan 内可创建定时器）
├── Heartbeat 上报
├── Plan 依赖管理（DAG 解析）
└── 失败重试策略
```

## 6. 文件结构

```
workspace/{agent_id}/
├── plans/                    # Plan 持久化
│   ├── index.json
│   └── {plan_id}.json
├── timers/                  # Timer 持久化
│   ├── index.json
│   └── {timer_id}.json
└── ...
```

## 7. 注意事项

1. **幂等性**：Timer 触发动作应保证幂等
2. **状态一致性**：每次状态变更立即持久化
3. **并发安全**：Timer Service 单线程执行，避免竞态
4. **优雅退出**：Agent 停止时保存所有状态，保留到下一个启动周期
