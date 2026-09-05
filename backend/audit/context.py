from contextvars import ContextVar
from typing import Optional

# Global context variables for implicit tracing and auditing
current_trace_id: ContextVar[Optional[str]] = ContextVar("current_trace_id", default=None)
current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)
current_session_id: ContextVar[Optional[str]] = ContextVar("current_session_id", default=None)
current_role: ContextVar[Optional[str]] = ContextVar("current_role", default=None)
