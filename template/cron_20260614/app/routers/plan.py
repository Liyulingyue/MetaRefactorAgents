from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from app.core.plan import Plan, Task
from app.core.tools import get_plan_service, PlanService

router = APIRouter()


class CreatePlanRequest(BaseModel):
    name: str
    description: str = ""
    tasks: List[dict] = []


class AddTaskRequest(BaseModel):
    name: str
    description: str = ""
    action: str
    params: dict = {}
    depends_on: List[str] = []


class UpdateTaskStatusRequest(BaseModel):
    status: str
    result: Optional[dict] = None


@router.get("/", response_model=List[dict])
async def list_plans(service: PlanService = Depends(get_plan_service)):
    return service.list_plans()


@router.post("/", response_model=dict)
async def create_plan(
    request: CreatePlanRequest,
    service: PlanService = Depends(get_plan_service)
):
    plan = service.create_plan(
        name=request.name,
        description=request.description,
        tasks=request.tasks if request.tasks else None
    )
    return plan.to_dict()


@router.get("/{plan_id}", response_model=dict)
async def get_plan(plan_id: str, service: PlanService = Depends(get_plan_service)):
    plan = service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan.to_dict()


@router.delete("/{plan_id}")
async def delete_plan(plan_id: str, service: PlanService = Depends(get_plan_service)):
    if not service.delete_plan(plan_id):
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"status": "success", "message": f"Plan {plan_id} deleted"}


@router.post("/{plan_id}/tasks", response_model=dict)
async def add_task(
    plan_id: str,
    request: AddTaskRequest,
    service: PlanService = Depends(get_plan_service)
):
    task = service.add_task(plan_id, request.dict())
    if not task:
        raise HTTPException(status_code=404, detail="Plan not found")
    return task.dict()


@router.patch("/{plan_id}/tasks/{task_id}/status", response_model=dict)
async def update_task_status(
    plan_id: str,
    task_id: str,
    request: UpdateTaskStatusRequest,
    service: PlanService = Depends(get_plan_service)
):
    task = service.update_task_status(plan_id, task_id, request.status, request.result)
    if not task:
        raise HTTPException(status_code=404, detail="Plan or task not found")
    return task.dict()


@router.post("/{plan_id}/next")
async def execute_next_task(plan_id: str, service: PlanService = Depends(get_plan_service)):
    result = service.execute_next_task(plan_id)
    if result is None:
        return {"status": "completed", "message": "All tasks completed", "plan_id": plan_id}
    return result


@router.post("/{plan_id}/pause")
async def pause_plan(plan_id: str, service: PlanService = Depends(get_plan_service)):
    plan = service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.status = "paused"
    service.update_plan(plan)
    return plan.to_dict()


@router.post("/{plan_id}/resume")
async def resume_plan(plan_id: str, service: PlanService = Depends(get_plan_service)):
    plan = service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.status = "active"
    service.update_plan(plan)
    return plan.to_dict()
