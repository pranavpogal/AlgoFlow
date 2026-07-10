from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.runtime.adk_runtime import AdkCoordinatorRuntime, MentorRoutingInput
from app.runtime.trajectory import Trajectory


def evaluate_adk_live_runtime_cases(path: str | Path) -> dict[str, Any]:
    cases = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    results = [asyncio.run(_evaluate_case(case)) for case in cases]
    return {
        "case_count": len(results),
        "passed": sum(result["passed"] for result in results),
        "failed": [result for result in results if not result["passed"]],
        "live_boundary_accuracy": _rate(results, "live_boundary_ok"),
        "live_fallback_accuracy": _rate(results, "fallback_ok"),
        "trajectory_event_coverage": _rate(results, "events_ok"),
        "deterministic_parity_accuracy": _rate(results, "route_ok"),
        "results": results,
    }


async def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    payload = case["input"]
    runtime = _runtime_for_case(case)
    trajectory = Trajectory.start("adk_live_runtime_eval", session_id=f"eval_{case['case_id']}")
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
    trajectory.finish()
    event_types = [event.event_type.value for event in trajectory.events]
    route_ok = (
        decision.selected_capability == case["expected_capability"]
        and decision.selected_skill == case["expected_skill"]
    )
    runtime_ok = trajectory.runtime_mode.value == case["expected_runtime_mode"]
    fallback_ok = trajectory.fallback_used is case["expected_fallback_used"]
    events_ok = set(case["required_events"]).issubset(event_types)
    live_boundary_ok = runtime_ok and events_ok
    return {
        "case_id": case["case_id"],
        "split": case.get("split", "development"),
        "mode": case["mode"],
        "route_ok": route_ok,
        "runtime_ok": runtime_ok,
        "fallback_ok": fallback_ok,
        "events_ok": events_ok,
        "live_boundary_ok": live_boundary_ok,
        "event_types": event_types,
        "runtime_mode": trajectory.runtime_mode.value,
        "fallback_used": trajectory.fallback_used,
        "trajectory": trajectory.to_dict(),
        "passed": all([route_ok, runtime_ok, fallback_ok, events_ok]),
    }


def _runtime_for_case(case: dict[str, Any]) -> AdkCoordinatorRuntime:
    mode = case["mode"]
    if mode == "disabled":
        return AdkCoordinatorRuntime(settings=Settings(enable_live_adk=False))
    if mode == "no_key":
        return AdkCoordinatorRuntime(settings=Settings(enable_live_adk=True, google_api_key=None))
    if mode == "mock_live_valid":
        async def valid_invoker(agent, routing_input, trajectory):
            return {
                "selected_capability": case["expected_capability"],
                "selected_skill": case["expected_skill"],
                "confidence": 0.91,
                "rationale": "Mock live ADK boundary returned expected route.",
                "fallback_allowed": True,
            }

        return AdkCoordinatorRuntime(settings=Settings(enable_live_adk=True), invoker=valid_invoker)
    if mode == "mock_live_invalid":
        async def invalid_invoker(agent, routing_input, trajectory):
            return {"selected_capability": "unsupported"}

        return AdkCoordinatorRuntime(settings=Settings(enable_live_adk=True), invoker=invalid_invoker)
    raise ValueError(f"Unsupported ADK live runtime eval mode: {mode}")


def _rate(results: list[dict[str, Any]], field: str) -> float:
    if not results:
        return 0.0
    return round(sum(1 for result in results if result[field]) / len(results), 3)
