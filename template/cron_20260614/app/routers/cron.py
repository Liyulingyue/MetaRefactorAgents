"""Cron API router."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.cron_types import CronSchedule, CronJob
from app.core.cron_service import CronService


router = APIRouter(prefix="/cron", tags=["cron"])

_cron_service: Optional[CronService] = None


def get_cron_service() -> CronService:
    if _cron_service is None:
        raise RuntimeError("Cron service not initialized")
    return _cron_service


def set_cron_service(service: CronService) -> None:
    global _cron_service
    _cron_service = service


class CreateCronRequest(BaseModel):
    name: str
    kind: str = "every"
    every_ms: Optional[int] = None
    at_ms: Optional[int] = None
    expr: Optional[str] = None
    tz: Optional[str] = None
    message: str = ""
    session_key: Optional[str] = None
    delete_after_run: bool = False


class UpdateCronRequest(BaseModel):
    name: Optional[str] = None
    kind: Optional[str] = None
    every_ms: Optional[int] = None
    at_ms: Optional[int] = None
    expr: Optional[str] = None
    tz: Optional[str] = None
    message: Optional[str] = None
    session_key: Optional[str] = None
    delete_after_run: Optional[bool] = None


@router.get("/", response_model=dict)
async def list_crons(include_disabled: bool = False):
    """List all cron jobs."""
    service = get_cron_service()
    jobs = service.list_jobs(include_disabled=include_disabled)
    return {
        "jobs": [j.to_dict() for j in jobs],
        "total": len(jobs),
    }


@router.get("/{job_id}", response_model=dict)
async def get_cron(job_id: str):
    """Get a cron job by ID."""
    service = get_cron_service()
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.post("/", response_model=dict)
async def create_cron(req: CreateCronRequest):
    """Create a new cron job."""
    service = get_cron_service()

    schedule = CronSchedule(
        kind=req.kind,
        at_ms=req.at_ms,
        every_ms=req.every_ms,
        expr=req.expr,
        tz=req.tz,
    )

    job = service.add_job(
        name=req.name,
        schedule=schedule,
        message=req.message,
        session_key=req.session_key,
        delete_after_run=req.delete_after_run,
    )
    return job.to_dict()


@router.post("/{job_id}/enable", response_model=dict)
async def enable_cron(job_id: str):
    """Enable a cron job."""
    service = get_cron_service()
    job = service.enable_job(job_id, enabled=True)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.post("/{job_id}/disable", response_model=dict)
async def disable_cron(job_id: str):
    """Disable a cron job."""
    service = get_cron_service()
    job = service.enable_job(job_id, enabled=False)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.delete("/{job_id}")
async def delete_cron(job_id: str):
    """Delete a cron job."""
    service = get_cron_service()
    result = service.remove_job(job_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    if result == "protected":
        raise HTTPException(status_code=403, detail="Cannot delete protected system job")
    return {"status": "removed"}


@router.patch("/{job_id}", response_model=dict)
async def update_cron(job_id: str, req: UpdateCronRequest):
    """Update a cron job."""
    service = get_cron_service()

    schedule = None
    if req.kind or req.every_ms is not None or req.at_ms is not None or req.expr is not None or req.tz is not None:
        existing = service.get_job(job_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Job not found")
        schedule = CronSchedule(
            kind=req.kind or existing.schedule.kind,
            at_ms=req.at_ms if req.at_ms is not None else existing.schedule.at_ms,
            every_ms=req.every_ms if req.every_ms is not None else existing.schedule.every_ms,
            expr=req.expr if req.expr is not None else existing.schedule.expr,
            tz=req.tz if req.tz is not None else existing.schedule.tz,
        )

    result = service.update_job(
        job_id,
        name=req.name,
        schedule=schedule,
        message=req.message,
        session_key=req.session_key,
        delete_after_run=req.delete_after_run,
    )
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    if result == "protected":
        raise HTTPException(status_code=403, detail="Cannot update protected system job")
    return result.to_dict()


@router.post("/{job_id}/run", response_model=dict)
async def run_cron(job_id: str, force: bool = False):
    """Manually run a cron job."""
    service = get_cron_service()
    success = await service.run_job(job_id, force=force)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or disabled")
    return {"status": "ok"}


@router.get("/status", response_model=dict)
async def cron_status():
    """Get cron service status."""
    service = get_cron_service()
    return service.status()