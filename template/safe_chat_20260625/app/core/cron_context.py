"""Context variables for cron job execution.

These contextvars allow the cron callback to mark the current execution
context (silent / alert sink) and have them be visible to Agent code
running on the same task, without leaking to other concurrent tasks.
"""

import contextvars
from typing import List, Optional

SILENT_CRON_CTX: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "silent_cron", default=False
)

ALERT_SINK_CTX: contextvars.ContextVar[Optional[List[str]]] = contextvars.ContextVar(
    "alert_sink", default=None
)
