from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from time import perf_counter
from typing import Any
from uuid import uuid4

from app.core.request_context import get_request_context

TRAJECTORY_SCHEMA_VERSION = "trajectory-v1"


class RuntimeMode(StrEnum):
    DETERMINISTIC_FALLBACK = "deterministic_fallback"
    ADK_DISABLED = "adk_disabled"
    ADK_MOCKED = "adk_mocked"
    ADK_LIVE = "adk_live"
    ADK_FALLBACK = "adk_fallback"


class TrajectoryEventType(StrEnum):
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    ADK_AGENT_BUILT = "ADK_AGENT_BUILT"
    ADK_INVOCATION_SKIPPED = "ADK_INVOCATION_SKIPPED"
    ADK_INVOCATION_STARTED = "ADK_INVOCATION_STARTED"
    ADK_INVOCATION_COMPLETED = "ADK_INVOCATION_COMPLETED"
    ADK_INVOCATION_FAILED = "ADK_INVOCATION_FAILED"
    ADK_LIVE_EVENT_RECEIVED = "ADK_LIVE_EVENT_RECEIVED"
    ADK_TOOL_REQUESTED = "ADK_TOOL_REQUESTED"
    ROUTE_SELECTED = "ROUTE_SELECTED"
    STRUCTURAL_POLICY_EVALUATED = "STRUCTURAL_POLICY_EVALUATED"
    SEMANTIC_POLICY_EVALUATED = "SEMANTIC_POLICY_EVALUATED"
    TOOL_CALL_COMPLETED = "TOOL_CALL_COMPLETED"
    TOOL_CALL_DENIED = "TOOL_CALL_DENIED"
    DETERMINISTIC_FALLBACK_USED = "DETERMINISTIC_FALLBACK_USED"
    WORKFLOW_EXECUTED = "WORKFLOW_EXECUTED"
    RESPONSE_VALIDATED = "RESPONSE_VALIDATED"


@dataclass(frozen=True)
class TrajectoryEvent:
    event_type: TrajectoryEventType
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    agent_id: str | None = None
    selected_skill: str | None = None
    tool_name: str | None = None
    model_name: str | None = None
    latency_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "selected_skill": self.selected_skill,
            "tool_name": self.tool_name,
            "model_name": self.model_name,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
        }


@dataclass
class Trajectory:
    trajectory_id: str
    task: str
    session_id: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    runtime_mode: RuntimeMode = RuntimeMode.DETERMINISTIC_FALLBACK
    schema_version: str = TRAJECTORY_SCHEMA_VERSION
    events: list[TrajectoryEvent] = field(default_factory=list)
    selected_capability: str | None = None
    fallback_used: bool = False
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str | None = None
    duration_ms: float | None = None
    _start: float = field(default_factory=perf_counter, repr=False)

    @classmethod
    def start(cls, task: str, session_id: str | None = None) -> "Trajectory":
        context = get_request_context()
        return cls(
            trajectory_id=f"traj_{uuid4().hex}",
            task=task,
            session_id=session_id or f"session_{uuid4().hex}",
            request_id=context.request_id if context else None,
            trace_id=context.trace_id if context else None,
        )

    def add(self, event_type: TrajectoryEventType, message: str, **kwargs: Any) -> None:
        self.events.append(TrajectoryEvent(event_type=event_type, message=message, **kwargs))

    def finish(self) -> None:
        self.finished_at = datetime.now(UTC).isoformat()
        self.duration_ms = round((perf_counter() - self._start) * 1000, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trajectory_id": self.trajectory_id,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "task": self.task,
            "runtime_mode": self.runtime_mode.value,
            "selected_capability": self.selected_capability,
            "fallback_used": self.fallback_used,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "events": [event.to_dict() for event in self.events],
        }
