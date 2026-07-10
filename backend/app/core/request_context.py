from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    trace_id: str


_current_request_context: ContextVar[RequestContext | None] = ContextVar(
    "current_request_context", default=None
)


def new_request_context(request_id: str | None = None, trace_id: str | None = None) -> RequestContext:
    return RequestContext(
        request_id=request_id or f"req_{uuid4().hex}",
        trace_id=trace_id or f"trace_{uuid4().hex}",
    )


def set_request_context(context: RequestContext):
    return _current_request_context.set(context)


def reset_request_context(token) -> None:
    _current_request_context.reset(token)


def get_request_context() -> RequestContext | None:
    return _current_request_context.get()
