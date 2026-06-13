import os
import json
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

PLANS_DIR = "plans"


class Task(BaseModel):
    id: str = ""
    name: str
    description: str = ""
    action: str
    params: dict = {}
    status: str = "pending"
    result: Optional[dict] = None
    created_at: str = ""
    updated_at: str = ""
    depends_on: List[str] = []

    def __init__(self, **data):
        if not data.get("id"):
            data["id"] = str(uuid.uuid4())[:8]
        if not data.get("created_at"):
            data["created_at"] = datetime.now().isoformat()
        if not data.get("updated_at"):
            data["updated_at"] = datetime.now().isoformat()
        super().__init__(**data)


class Plan(BaseModel):
    id: str = ""
    name: str
    description: str = ""
    tasks: List[Task] = []
    status: str = "pending"
    created_at: str = ""
    updated_at: str = ""
    current_task_index: int = 0

    def __init__(self, **data):
        if not data.get("id"):
            data["id"] = str(uuid.uuid4())[:8]
        if not data.get("created_at"):
            data["created_at"] = datetime.now().isoformat()
        super().__init__(**data)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tasks": [t.dict() for t in self.tasks],
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_task_index": self.current_task_index,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        tasks = [Task(**t) for t in data.get("tasks", [])]
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            tasks=tasks,
            status=data.get("status", "pending"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            current_task_index=data.get("current_task_index", 0),
        )


class PlanService:
    def __init__(self, workspace_dir: str = "."):
        self.plans_dir = os.path.join(workspace_dir, PLANS_DIR)
        os.makedirs(self.plans_dir, exist_ok=True)

    def _get_plan_path(self, plan_id: str) -> str:
        return os.path.join(self.plans_dir, f"{plan_id}.json")

    def _update_index(self, plan_ids: List[str]):
        index_path = os.path.join(self.plans_dir, "index.json")
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({"plans": plan_ids}, f, indent=2)

    def list_plans(self) -> List[dict]:
        index_path = os.path.join(self.plans_dir, "index.json")
        if not os.path.exists(index_path):
            return []
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        plan_ids = data.get("plans", [])
        plans = []
        for pid in plan_ids:
            plan = self.get_plan(pid)
            if plan:
                plans.append(plan.to_dict())
        return plans

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        path = self._get_plan_path(plan_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Plan.from_dict(data)

    def create_plan(self, name: str, description: str = "", tasks: Optional[List[dict]] = None) -> Plan:
        plan = Plan(name=name, description=description)
        if tasks:
            plan.tasks = [Task(**t) for t in tasks]

        with open(self._get_plan_path(plan.id), "w", encoding="utf-8") as f:
            json.dump(plan.to_dict(), f, indent=2)

        index_path = os.path.join(self.plans_dir, "index.json")
        plan_ids = []
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                plan_ids = json.load(f).get("plans", [])
        plan_ids.append(plan.id)
        self._update_index(plan_ids)

        return plan

    def update_plan(self, plan: Plan) -> Plan:
        plan.updated_at = datetime.now().isoformat()
        with open(self._get_plan_path(plan.id), "w", encoding="utf-8") as f:
            json.dump(plan.to_dict(), f, indent=2)
        return plan

    def delete_plan(self, plan_id: str) -> bool:
        path = self._get_plan_path(plan_id)
        if not os.path.exists(path):
            return False

        os.remove(path)

        index_path = os.path.join(self.plans_dir, "index.json")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                plan_ids = json.load(f).get("plans", [])
            plan_ids = [pid for pid in plan_ids if pid != plan_id]
            self._update_index(plan_ids)

        return True

    def add_task(self, plan_id: str, task_data: dict) -> Optional[Task]:
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        task = Task(**task_data)
        plan.tasks.append(task)
        self.update_plan(plan)
        return task

    def update_task_status(self, plan_id: str, task_id: str, status: str, result: Optional[dict] = None) -> Optional[Task]:
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        for task in plan.tasks:
            if task.id == task_id:
                task.status = status
                task.updated_at = datetime.now().isoformat()
                if result:
                    task.result = result
                break
        else:
            return None

        if status in ("completed", "failed"):
            all_done = all(t.status in ("completed", "failed") for t in plan.tasks)
            if all_done:
                plan.status = "completed" if status == "completed" else "failed"

        self.update_plan(plan)
        return task

    def get_next_task(self, plan_id: str) -> Optional[Task]:
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        # 遍历所有任务，寻找第一个状态为 pending 且满足依赖关系的任务
        for task in plan.tasks:
            if task.status == "pending" and self.can_execute_task(plan, task):
                return task
        return None

    def execute_next_task(self, plan_id: str) -> Optional[dict]:
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        task = self.get_next_task(plan_id)
        if not task:
            plan.status = "completed"
            self.update_plan(plan)
            return None

        plan.current_task_index = plan.tasks.index(task)
        task.status = "running"
        self.update_plan(plan)

        return {
            "plan_id": plan_id,
            "task": task.dict(),
            "status": "ready_to_execute",
        }

    def can_execute_task(self, plan: Plan, task: Task) -> bool:
        for dep_id in task.depends_on:
            for t in plan.tasks:
                if t.id == dep_id and t.status != "completed":
                    return False
        return True
