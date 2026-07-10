from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from app.core.auth import Principal
from app.core.config import Settings
from app.core.semantic_policy import MentoringMode, SemanticPolicyContext
from app.core.tool_gateway import tool_gateway
from app.runtime.adk_runtime import AdkCoordinatorRuntime, MentorRoutingInput
from app.runtime.trajectory import Trajectory
from app.skills.progressive_hinting.workflow import detect_intent


def evaluate_adk_routing_cases(path: str | Path) -> dict[str, Any]:
    cases = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    results = [_evaluate_case(case) for case in cases]
    failures = [result for result in results if not result["passed"]]
    return {
        "case_count": len(results),
        "passed": len(results) - len(failures),
        "failed": failures,
        "routing_accuracy": _rate(results, "route_ok"),
        "trajectory_event_coverage": _rate(results, "events_ok"),
        "trajectory_identity_completeness": _rate(results, "identity_ok"),
        "fallback_policy_accuracy": _rate(results, "fallback_ok"),
        "results": results,
    }


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    result = asyncio.run(_evaluate_case_async(case))
    return result


async def _evaluate_case_async(case: dict[str, Any]) -> dict[str, Any]:
    runtime = AdkCoordinatorRuntime(settings=Settings(enable_live_adk=False))
    payload = case["input"]
    trajectory = Trajectory.start("adk_routing_eval", session_id=f"eval_{case['case_id']}")
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
    if decision.selected_capability in {"problem_analysis", "next_hint"}:
        tool_gateway.call(
            "problem.detect_pattern",
            {"title": payload["title"], "description": payload["description"]},
            caller="adk_narrow_coordinator",
            principal=Principal(user_id="eval-user", auth_mode="eval"),
            trajectory=trajectory,
            semantic_context=_semantic_context(payload, decision.selected_capability, trajectory),
        )
    trajectory.finish()
    event_types = [event.event_type.value for event in trajectory.events]
    route_ok = (
        decision.selected_capability == case["expected_capability"]
        and decision.selected_skill == case["expected_skill"]
    )
    events_ok = set(case["required_events"]).issubset(event_types)
    payload = trajectory.to_dict()
    identity_ok = all(
        [
            payload.get("trajectory_id", "").startswith("traj_"),
            payload.get("session_id") == f"eval_{case['case_id']}",
            payload.get("schema_version") == "trajectory-v1",
        ]
    )
    fallback_ok = trajectory.fallback_used is case["expected_fallback_used"]
    return {
        "case_id": case["case_id"],
        "expected_capability": case["expected_capability"],
        "actual_capability": decision.selected_capability,
        "expected_skill": case["expected_skill"],
        "actual_skill": decision.selected_skill,
        "route_ok": route_ok,
        "events_ok": events_ok,
        "identity_ok": identity_ok,
        "fallback_ok": fallback_ok,
        "event_types": event_types,
        "runtime_mode": trajectory.runtime_mode.value,
        "fallback_used": trajectory.fallback_used,
        "trajectory": payload,
        "passed": all([route_ok, events_ok, identity_ok, fallback_ok]),
    }


def _rate(results: list[dict[str, Any]], field: str) -> float:
    if not results:
        return 0.0
    return round(sum(1 for result in results if result[field]) / len(results), 3)


def _semantic_context(
    payload: dict[str, Any], selected_capability: str, trajectory: Trajectory
) -> SemanticPolicyContext:
    hint_intent = detect_intent(payload.get("user_message"), payload.get("reveal_solution", False))
    if selected_capability == "next_hint":
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
        requested_tool_id="problem.detect_pattern",
        operation_type="read",
        tool_arguments={"title": payload["title"], "description": payload["description"]},
        task_context={
            "title": payload["title"],
            "description": payload["description"],
            "user_message": payload.get("user_message", ""),
        },
        trusted_context={"runtime": "adk_routing_eval"},
        reveal_authorized=bool(payload.get("reveal_solution", False) and hint_intent.value == "FULL_SOLUTION"),
    )
