from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings, get_settings
from app.runtime.trajectory import RuntimeMode, Trajectory, TrajectoryEventType

try:
    from google.adk.agents import Agent
except Exception:  # pragma: no cover - local dependency guard
    Agent = None  # type: ignore[assignment]

try:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as genai_types
except Exception:  # pragma: no cover - local dependency guard
    Runner = None  # type: ignore[assignment]
    InMemorySessionService = None  # type: ignore[assignment]
    genai_types = None  # type: ignore[assignment]

CoordinatorCapability = Literal[
    "problem_analysis",
    "next_hint",
    "recommendations",
    "pattern_transfer",
    "code_review",
    "study_plan",
]
CoordinatorToolId = Literal["problem.detect_pattern", "problem.related_problems", "code.review_static"]


class CoordinatorToolRequest(BaseModel):
    tool_id: CoordinatorToolId
    purpose: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


class CoordinatorDecision(BaseModel):
    selected_capability: CoordinatorCapability
    selected_skill: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    fallback_allowed: bool = True
    tool_requests: list[CoordinatorToolRequest] = Field(default_factory=list)


@dataclass(frozen=True)
class MentorRoutingInput:
    requested_capability: str | None
    user_message: str | None
    title: str
    description: str
    current_hint_level: int | None = None
    reveal_solution: bool = False


AdkDecisionInvoker = Callable[[Any, MentorRoutingInput, Trajectory], Awaitable[dict[str, Any]]]


class LiveAdkInvocationError(RuntimeError):
    """Raised when the bounded live ADK path cannot produce a valid routing payload."""


class LiveAdkDecisionInvoker:
    """Small live ADK runner wrapper for the narrow coordinator route.

    This intentionally invokes only the coordinator agent and exposes no tools to ADK. Tool
    execution remains outside the model path and must still pass through ToolGateway.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def __call__(
        self, agent: Any, routing_input: MentorRoutingInput, trajectory: Trajectory
    ) -> dict[str, Any]:
        if Runner is None or InMemorySessionService is None or genai_types is None:
            raise LiveAdkInvocationError("Google ADK runner dependencies are unavailable.")
        if agent is None:
            raise LiveAdkInvocationError("Google ADK agent is unavailable.")
        if self.settings.google_api_key:
            os.environ.setdefault("GOOGLE_API_KEY", self.settings.google_api_key)

        runner = Runner(
            app_name="algoflow",
            agent=agent,
            session_service=InMemorySessionService(),
            auto_create_session=True,
        )
        message = genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=self._prompt(routing_input))],
        )
        raw_response = ""
        event_count = 0
        async with asyncio.timeout(self.settings.live_adk_timeout_seconds):
            async for event in runner.run_async(
                user_id="algoflow-runtime",
                session_id=trajectory.session_id or "algoflow-live-session",
                new_message=message,
            ):
                event_count += 1
                trajectory.add(
                    TrajectoryEventType.ADK_LIVE_EVENT_RECEIVED,
                    "Live ADK runner yielded an event.",
                    agent_id=AdkCoordinatorRuntime.agent_name,
                    metadata={
                        "event_author": getattr(event, "author", None),
                        "is_final_response": event.is_final_response()
                        if hasattr(event, "is_final_response")
                        else False,
                        "has_output": getattr(event, "output", None) is not None,
                    },
                )
                raw_response = _extract_event_payload(event) or raw_response
                if event_count >= self.settings.live_adk_max_events:
                    break

        if not raw_response:
            raise LiveAdkInvocationError("Live ADK invocation returned no parseable content.")
        payload = _parse_json_payload(raw_response)
        return CoordinatorDecision.model_validate(payload).model_dump()

    def _prompt(self, routing_input: MentorRoutingInput) -> str:
        return (
            "Route this AlgoFlow request. Return only JSON matching this schema: "
            "{selected_capability: 'problem_analysis'|'next_hint'|'recommendations'|'pattern_transfer'|'code_review'|'study_plan', "
            "selected_skill: string, "
            "confidence: number, rationale: string, fallback_allowed: boolean, "
            "tool_requests: optional array of {tool_id: 'problem.detect_pattern'|'problem.related_problems'|'code.review_static', "
            "purpose: string, arguments: object}}. "
            "Do not solve the coding problem. Do not execute tools. You may only request a tool "
            "when the selected capability needs it, and the server will independently approve or deny it. "
            f"requested_capability={routing_input.requested_capability!r}; "
            f"user_message={routing_input.user_message!r}; "
            f"title={routing_input.title!r}; "
            f"current_hint_level={routing_input.current_hint_level!r}; "
            f"reveal_solution={routing_input.reveal_solution!r}."
        )


class AdkCoordinatorRuntime:
    """Bounded ADK coordinator for the first narrow routing slice.

    The runtime creates a real Google ADK Agent when the dependency is available, but live model
    invocation is disabled unless configuration and an explicit invoker allow it. This keeps CI and
    local development deterministic while making the ADK boundary concrete and testable.
    """

    agent_name = "algoflow_narrow_coordinator"
    agent_version = "adk-routing-v1"

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        invoker: AdkDecisionInvoker | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.invoker = invoker or self._default_invoker()
        self.agent = self._build_agent()

    async def route(self, routing_input: MentorRoutingInput, trajectory: Trajectory) -> CoordinatorDecision:
        trajectory.add(
            TrajectoryEventType.REQUEST_RECEIVED,
            "Coordinator routing request received.",
            metadata={
                "requested_capability": routing_input.requested_capability,
                "has_user_message": bool(routing_input.user_message),
            },
        )
        trajectory.add(
            TrajectoryEventType.ADK_AGENT_BUILT,
            "Narrow ADK coordinator agent is available for routing boundary.",
            agent_id=self.agent_name,
            model_name=self.settings.gemini_model,
            metadata={"agent_version": self.agent_version, "agent_available": self.agent is not None},
        )
        if not self.settings.enable_live_adk:
            trajectory.runtime_mode = RuntimeMode.ADK_DISABLED
            trajectory.fallback_used = True
            trajectory.add(
                TrajectoryEventType.ADK_INVOCATION_SKIPPED,
                "ENABLE_LIVE_ADK is false; using deterministic routing fallback.",
                agent_id=self.agent_name,
            )
            return self._deterministic_decision(routing_input, trajectory)
        if self.invoker is None:
            trajectory.runtime_mode = RuntimeMode.ADK_FALLBACK
            trajectory.fallback_used = True
            trajectory.add(
                TrajectoryEventType.ADK_INVOCATION_SKIPPED,
                "Live ADK was enabled but no bounded invoker or credentials are configured; using fallback.",
                agent_id=self.agent_name,
            )
            return self._deterministic_decision(routing_input, trajectory)

        trajectory.runtime_mode = (
            RuntimeMode.ADK_LIVE
            if isinstance(self.invoker, LiveAdkDecisionInvoker)
            else RuntimeMode.ADK_MOCKED
        )
        trajectory.add(
            TrajectoryEventType.ADK_INVOCATION_STARTED,
            "Bounded ADK coordinator invocation started.",
            agent_id=self.agent_name,
            model_name=self.settings.gemini_model,
        )
        try:
            raw_decision = await self.invoker(self.agent, routing_input, trajectory)
            decision = CoordinatorDecision.model_validate(raw_decision)
        except (ValidationError, Exception) as exc:
            trajectory.runtime_mode = RuntimeMode.ADK_FALLBACK
            trajectory.fallback_used = True
            trajectory.add(
                TrajectoryEventType.ADK_INVOCATION_FAILED,
                "ADK coordinator invocation failed validation; using deterministic fallback.",
                agent_id=self.agent_name,
                metadata={"error_type": type(exc).__name__},
            )
            return self._deterministic_decision(routing_input, trajectory)

        trajectory.add(
            TrajectoryEventType.ADK_INVOCATION_COMPLETED,
            "Bounded ADK coordinator returned a valid routing decision.",
            agent_id=self.agent_name,
            selected_skill=decision.selected_skill,
            metadata={"confidence": decision.confidence},
        )
        trajectory.selected_capability = decision.selected_capability
        trajectory.add(
            TrajectoryEventType.ROUTE_SELECTED,
            decision.rationale,
            agent_id=self.agent_name,
            selected_skill=decision.selected_skill,
            metadata={"source": "adk_coordinator", "confidence": decision.confidence},
        )
        return decision

    def _build_agent(self) -> Any:
        if Agent is None:
            return None
        return Agent(
            name=self.agent_name,
            model=self.settings.gemini_model,
            description="Narrow AlgoFlow coordinator for routing mentor requests to deterministic skills.",
            instruction=(
                "Route only between problem_analysis, next_hint, recommendations, pattern_transfer, code_review, and study_plan. "
                "Preserve learner agency. "
                "Never solve the problem. You may request only approved read/draft tools in the "
                "structured routing decision; never execute tools directly."
            ),
            output_schema=CoordinatorDecision,
            timeout=3.0,
            tools=[],
            sub_agents=[],
        )

    def _default_invoker(self) -> AdkDecisionInvoker | None:
        if not self.settings.enable_live_adk:
            return None
        if not self.settings.google_api_key:
            return None
        return LiveAdkDecisionInvoker(self.settings)

    def _deterministic_decision(
        self, routing_input: MentorRoutingInput, trajectory: Trajectory
    ) -> CoordinatorDecision:
        requested = (routing_input.requested_capability or "").strip().lower()
        message = (routing_input.user_message or "").lower()
        if requested in {"next_hint", "hint", "progressive_hinting"}:
            capability: CoordinatorCapability = "next_hint"
            skill = "progressive_hinting_workflow"
        elif requested in {"study_plan", "study-plan", "planner", "study_planner", "plan"}:
            capability = "study_plan"
            skill = "study_planning_workflow"
        elif requested in {"code_review", "review_code", "code-review", "review"}:
            capability = "code_review"
            skill = "code_review_workflow"
        elif requested in {"pattern_transfer", "transfer", "transfer_learning", "pattern-transfer"}:
            capability = "pattern_transfer"
            skill = "pattern_transfer_workflow"
        elif requested in {"recommendations", "recommendation", "related_problems", "pattern_recommendation"}:
            capability = "recommendations"
            skill = "pattern_recommendation_workflow"
        elif requested in {"problem_analysis", "analyze_problem", "classification"}:
            capability = "problem_analysis"
            skill = "problem_intelligence_workflow"
        elif "review my code" in message or "code review" in message or "find the bug" in message:
            capability = "code_review"
            skill = "code_review_workflow"
        elif "study plan" in message or "plan my prep" in message or "days remaining" in message:
            capability = "study_plan"
            skill = "study_planning_workflow"
        elif "pattern transfer" in message or "transfer this pattern" in message or "pattern evolution" in message:
            capability = "pattern_transfer"
            skill = "pattern_transfer_workflow"
        elif "recommend" in message or "related problem" in message or "practice next" in message:
            capability = "recommendations"
            skill = "pattern_recommendation_workflow"
        elif "hint" in message or routing_input.current_hint_level is not None:
            capability = "next_hint"
            skill = "progressive_hinting_workflow"
        else:
            capability = "problem_analysis"
            skill = "problem_intelligence_workflow"
        decision = CoordinatorDecision(
            selected_capability=capability,
            selected_skill=skill,
            confidence=0.85,
            rationale="Deterministic fallback selected the least-autonomous matching workflow.",
            fallback_allowed=True,
        )
        trajectory.selected_capability = decision.selected_capability
        trajectory.add(
            TrajectoryEventType.DETERMINISTIC_FALLBACK_USED,
            decision.rationale,
            agent_id=self.agent_name,
            selected_skill=decision.selected_skill,
            metadata={"requested_capability": routing_input.requested_capability},
        )
        trajectory.add(
            TrajectoryEventType.ROUTE_SELECTED,
            decision.rationale,
            agent_id=self.agent_name,
            selected_skill=decision.selected_skill,
            metadata={"source": "deterministic_fallback", "confidence": decision.confidence},
        )
        return decision


adk_coordinator_runtime = AdkCoordinatorRuntime()


def _extract_event_payload(event: Any) -> str | None:
    output = getattr(event, "output", None)
    if isinstance(output, dict):
        return json.dumps(output)
    if isinstance(output, BaseModel):
        return output.model_dump_json()
    if isinstance(output, str) and output.strip():
        return output
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None) or []
    texts = [getattr(part, "text", None) for part in parts if getattr(part, "text", None)]
    if texts:
        return "\n".join(texts)
    return None


def _parse_json_payload(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.startswith("json"):
            candidate = candidate[4:].strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise LiveAdkInvocationError("Live ADK response did not contain JSON.") from None
        return json.loads(candidate[start : end + 1])
