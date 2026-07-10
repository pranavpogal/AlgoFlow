from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from app.core.auth import Principal
from app.core.config import Settings
from app.core.semantic_policy import MentoringMode, SemanticPolicyContext
from app.core.tool_gateway import ToolGatewayError, tool_gateway
from app.runtime.adk_runtime import AdkCoordinatorRuntime, CoordinatorToolRequest, MentorRoutingInput
from app.runtime.trajectory import Trajectory, TrajectoryEventType
from app.skills.progressive_hinting.workflow import detect_intent


def evaluate_adk_tool_orchestration_cases(path: str | Path) -> dict[str, Any]:
    cases = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    results = [asyncio.run(_evaluate_case(case)) for case in cases]
    return {
        "case_count": len(results),
        "passed": sum(result["passed"] for result in results),
        "failed": [result for result in results if not result["passed"]],
        "tool_request_execution_accuracy": _rate(results, "tool_execution_ok"),
        "tool_policy_enforcement_accuracy": _rate(results, "policy_enforcement_ok"),
        "tool_trajectory_coverage": _rate(results, "events_ok"),
        "tool_fallback_non_bypass_accuracy": _rate(results, "fallback_non_bypass_ok"),
        "results": results,
    }


async def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    payload = case["input"]
    runtime = _runtime_for_case(case)
    trajectory = Trajectory.start("adk_tool_orchestration_eval", session_id=f"eval_{case['case_id']}")
    decision = await runtime.route(
        MentorRoutingInput(
            requested_capability=payload.get("requested_capability"),
            user_message=payload.get("user_message"),
            title=payload["title"],
            description=payload["description"],
            current_hint_level=payload.get("current_hint_level"),
            reveal_solution=payload.get("reveal_solution", False),
        ),
        trajectory,
    )
    tool_records = []
    detected_pattern: str | None = None
    for tool_request in _tool_requests_for_route(decision):
        trusted_payload = _trusted_tool_payload(tool_request, payload, detected_pattern)
        trajectory.add(
            TrajectoryEventType.ADK_TOOL_REQUESTED,
            "Coordinator requested a policy-gated tool.",
            agent_id=AdkCoordinatorRuntime.agent_name,
            selected_skill=decision.selected_skill,
            tool_name=tool_request.tool_id,
            metadata={
                "tool_id": tool_request.tool_id,
                "purpose": tool_request.purpose,
                "provided_argument_keys": sorted(tool_request.arguments.keys()),
                "trusted_argument_keys": sorted(trusted_payload.keys()),
            },
        )
        try:
            result, record = tool_gateway.call(
                tool_request.tool_id,
                trusted_payload,
                caller="adk_narrow_coordinator",
                principal=Principal(user_id="eval-user", auth_mode="eval"),
                trajectory=trajectory,
                semantic_context=_semantic_context(
                    payload,
                    decision.selected_capability,
                    trajectory,
                    tool_request.tool_id,
                    trusted_payload,
                ),
            )
            tool_records.append(record.to_dict())
            if tool_request.tool_id == "problem.detect_pattern":
                detected_pattern = result.get("pattern")
        except ToolGatewayError as exc:
            if exc.record is not None:
                tool_records.append(exc.record.to_dict())
    trajectory.finish()

    event_types = [event.event_type.value for event in trajectory.events]
    expected = case["expected"]
    completed_ids = [record["tool_id"] for record in tool_records if record["success"]]
    denied_ids = [record["tool_id"] for record in tool_records if not record["success"]]
    reason_codes = [
        record["semantic_decision"]["reason_code"]
        for record in tool_records
        if record.get("semantic_decision")
    ]
    tool_execution_ok = completed_ids == expected.get("completed_tool_ids", [])
    policy_enforcement_ok = (
        denied_ids == expected.get("denied_tool_ids", [])
        and reason_codes == expected.get("semantic_reason_codes", reason_codes)
    )
    events_ok = set(expected["required_events"]).issubset(event_types)
    fallback_non_bypass_ok = not set(expected.get("denied_tool_ids", [])).intersection(completed_ids)
    route_ok = decision.selected_capability == expected["selected_capability"]
    return {
        "case_id": case["case_id"],
        "split": case.get("split", "development"),
        "mode": case["mode"],
        "route_ok": route_ok,
        "tool_execution_ok": tool_execution_ok,
        "policy_enforcement_ok": policy_enforcement_ok,
        "events_ok": events_ok,
        "fallback_non_bypass_ok": fallback_non_bypass_ok,
        "event_types": event_types,
        "completed_tool_ids": completed_ids,
        "denied_tool_ids": denied_ids,
        "semantic_reason_codes": reason_codes,
        "runtime_mode": trajectory.runtime_mode.value,
        "trajectory": trajectory.to_dict(),
        "tool_records": tool_records,
        "passed": all([route_ok, tool_execution_ok, policy_enforcement_ok, events_ok, fallback_non_bypass_ok]),
    }


def _runtime_for_case(case: dict[str, Any]) -> AdkCoordinatorRuntime:
    mode = case["mode"]
    if mode == "disabled_default_request":
        return AdkCoordinatorRuntime(settings=Settings(enable_live_adk=False))

    async def invoker(agent, routing_input, trajectory):
        return {
            "selected_capability": case["expected"]["selected_capability"],
            "selected_skill": case["expected"]["selected_skill"],
            "confidence": 0.9,
            "rationale": "Mock ADK route emitted bounded tool requests for orchestration eval.",
            "fallback_allowed": True,
            "tool_requests": case.get("tool_requests", []),
        }

    if mode in {"mock_detect_request", "mock_related_request", "mock_code_review_request"}:
        return AdkCoordinatorRuntime(settings=Settings(enable_live_adk=True), invoker=invoker)
    raise ValueError(f"Unsupported ADK tool orchestration eval mode: {mode}")


def _tool_requests_for_route(decision: Any) -> list[CoordinatorToolRequest]:
    if decision.tool_requests:
        return decision.tool_requests
    if decision.selected_capability in {"problem_analysis", "next_hint"}:
        return [
            CoordinatorToolRequest(
                tool_id="problem.detect_pattern",
                purpose="Default policy-gated pattern detection required by the selected workflow.",
                arguments={},
            )
        ]
    return []


def _trusted_tool_payload(
    tool_request: CoordinatorToolRequest, payload: dict[str, Any], detected_pattern: str | None
) -> dict[str, Any]:
    if tool_request.tool_id == "problem.detect_pattern":
        return {"title": payload["title"], "description": payload["description"]}
    if tool_request.tool_id == "problem.related_problems":
        requested_pattern = tool_request.arguments.get("pattern")
        pattern = detected_pattern or (requested_pattern if isinstance(requested_pattern, str) else None)
        return {"pattern": pattern or "Unknown"}
    if tool_request.tool_id == "code.review_static":
        return {
            "title": payload["title"],
            "language": payload.get("language", "unknown"),
            "code": payload.get("code", ""),
            "problem_description": payload.get("problem_description") or payload["description"],
            "user_intent": payload.get("user_message"),
        }
    return {}


def _semantic_context(
    payload: dict[str, Any],
    selected_capability: str,
    trajectory: Trajectory,
    tool_id: str,
    tool_arguments: dict[str, Any],
) -> SemanticPolicyContext:
    hint_intent = detect_intent(payload.get("user_message"), payload.get("reveal_solution", False))
    if selected_capability == "code_review":
        user_intent = "CODE_REVIEW"
        mentoring_mode = MentoringMode.CODE_REVIEW.value
    elif selected_capability == "pattern_transfer":
        user_intent = "RECOMMEND_TRANSFER"
        mentoring_mode = MentoringMode.RECOMMEND_TRANSFER.value
    elif selected_capability == "recommendations":
        user_intent = "RECOMMENDATION"
        mentoring_mode = MentoringMode.RECOMMEND_TRANSFER.value
    elif selected_capability == "next_hint":
        user_intent = hint_intent.value
        mentoring_mode = (
            MentoringMode.EXPLICIT_SOLUTION.value
            if hint_intent.value == "FULL_SOLUTION" and payload.get("reveal_solution", False)
            else MentoringMode.HINT_ONLY.value
        )
    else:
        user_intent = "PROBLEM_ANALYSIS"
        mentoring_mode = MentoringMode.EXPLAIN_CONCEPT.value
    return SemanticPolicyContext(
        principal_id="eval-user",
        request_id=trajectory.request_id,
        trace_id=trajectory.trace_id,
        session_id=trajectory.session_id,
        trajectory_id=trajectory.trajectory_id,
        caller_id="adk_narrow_coordinator",
        selected_capability=selected_capability,
        user_intent=user_intent,
        mentoring_mode=mentoring_mode,
        requested_tool_id=tool_id,
        operation_type="draft" if tool_id in {"problem.related_problems", "code.review_static"} else "read",
        tool_arguments=tool_arguments,
        task_context={
            "title": payload["title"],
            "description": payload["description"],
            "user_message": payload.get("user_message", ""),
        },
        trusted_context={"runtime": "adk_tool_orchestration_eval"},
        reveal_authorized=bool(payload.get("reveal_solution", False) and hint_intent.value == "FULL_SOLUTION"),
    )


def _rate(results: list[dict[str, Any]], field: str) -> float:
    if not results:
        return 0.0
    return round(sum(1 for result in results if result[field]) / len(results), 3)
