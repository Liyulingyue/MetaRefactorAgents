"""Cron types for scheduled tasks."""

from dataclasses import dataclass, field
from typing import Any, Literal, Optional
from datetime import datetime


@dataclass
class CronSchedule:
    """Schedule definition for a cron job."""
    kind: Literal["at", "every", "cron"] = "every"
    at_ms: Optional[int] = None
    every_ms: Optional[int] = None
    expr: Optional[str] = None
    tz: Optional[str] = None


@dataclass
class CronPayload:
    """What to do when the job runs."""
    kind: Literal["system_event", "agent_turn"] = "agent_turn"
    message: str = ""
    session_key: Optional[str] = None
    origin_channel: Optional[str] = None
    origin_chat_id: Optional[str] = None
    origin_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CronRunRecord:
    """A single execution record for a cron job."""
    run_at_ms: int
    status: Literal["ok", "error", "skipped"]
    duration_ms: int = 0
    error: Optional[str] = None


@dataclass
class CronJobState:
    """Runtime state of a job."""
    next_run_at_ms: Optional[int] = None
    last_run_at_ms: Optional[int] = None
    last_status: Optional[Literal["ok", "error", "skipped"]] = None
    last_error: Optional[str] = None
    run_history: list[CronRunRecord] = field(default_factory=list)


@dataclass
class CronJob:
    """A scheduled job."""
    id: str
    name: str
    enabled: bool = True
    schedule: CronSchedule = field(default_factory=lambda: CronSchedule(kind="every"))
    payload: CronPayload = field(default_factory=CronPayload)
    state: CronJobState = field(default_factory=CronJobState)
    created_at_ms: int = 0
    updated_at_ms: int = 0
    delete_after_run: bool = False

    @classmethod
    def from_dict(cls, kwargs: dict) -> "CronJob":
        state_kwargs = dict(kwargs.get("state", {}))
        state_kwargs["run_history"] = [
            record if isinstance(record, CronRunRecord) else CronRunRecord(**record)
            for record in state_kwargs.get("run_history", [])
        ]
        kwargs["schedule"] = CronSchedule(**kwargs.get("schedule", {"kind": "every"}))
        kwargs["payload"] = CronPayload(**kwargs.get("payload", {}))
        kwargs["state"] = CronJobState(**state_kwargs)
        return cls(**kwargs)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "schedule": {
                "kind": self.schedule.kind,
                "atMs": self.schedule.at_ms,
                "everyMs": self.schedule.every_ms,
                "expr": self.schedule.expr,
                "tz": self.schedule.tz,
            },
            "payload": {
                "kind": self.payload.kind,
                "message": self.payload.message,
                "sessionKey": self.payload.session_key,
                "originChannel": self.payload.origin_channel,
                "originChatId": self.payload.origin_chat_id,
                "originMetadata": self.payload.origin_metadata,
            },
            "state": {
                "nextRunAtMs": self.state.next_run_at_ms,
                "lastRunAtMs": self.state.last_run_at_ms,
                "lastStatus": self.state.last_status,
                "lastError": self.state.last_error,
                "runHistory": [
                    {
                        "runAtMs": r.run_at_ms,
                        "status": r.status,
                        "durationMs": r.duration_ms,
                        "error": r.error,
                    }
                    for r in self.state.run_history
                ],
            },
            "createdAtMs": self.created_at_ms,
            "updatedAtMs": self.updated_at_ms,
            "deleteAfterRun": self.delete_after_run,
        }


@dataclass
class CronStore:
    """Persistent store for cron jobs."""
    version: int = 1
    jobs: list[CronJob] = field(default_factory=list)