"""Thread-local context for current request session."""

import contextvars

_session_context: contextvars.ContextVar[str | None] = contextvars.ContextVar("session_key", default=None)


def set_current_session(session_key: str | None) -> None:
    """Set the current session key for this async context."""
    _session_context.set(session_key)


def get_current_session() -> str | None:
    """Get the current session key from this async context."""
    return _session_context.get()


class SessionContext:
    """Context manager for setting current session."""

    def __init__(self, session_key: str | None):
        self.session_key = session_key
        self._token = None

    def __enter__(self):
        self._token = _session_context.set(self.session_key)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _session_context.reset(self._token)
        return False
