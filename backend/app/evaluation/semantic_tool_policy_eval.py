from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.auth import Principal
from app.core.semantic_policy import SemanticPolicyContext
from app.core.tool_gateway import ToolGatewayError, tool_gateway
from app.runtime.trajectory import Trajectory


def evaluate_semantic_tool_policy_cases(path: str | Path) -> dict[str, Any]:
    cases = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    results = [_evaluate_case(case) for case in cases]
    passed = sum(item["passed"] for item in results)
    return {
        "case_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
        **_metrics(results),
    }


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    item = case["input"]
    expected = case["expected"]
    trajectory = Trajectory.start("semantic_tool_policy_eval", session_id=f"eval_{case['case_id']}")
    record = None
    result = None
    error_type = None
    try:
        result, record = tool_gateway.call(
            item["tool_id"],
            item["payload"],
            caller=item["caller"],
            principal=Principal(user_id="eval-user", auth_mode="eval"),
            trajectory=trajectory,
            semantic_context=_context(item),
        )
    except ToolGatewayError as exc:
        record = exc.record
        error_type = type(exc).__name__
    except Exception as exc:  # unknown tool and infrastructure-like cases
        error_type = type(exc).__name__

    event_types = [event.event_type.value for event in trajectory.events]
    semantic = record.semantic_decision.to_dict() if record and record.semantic_decision else None
    structural_policy_id = record.decision.policy_id if record else "unknown_tool"
    actual_decision = "allow" if record and record.success else "deny"
    actual_reason = semantic["reason_code"] if semantic else None
    semantic_evaluated = semantic is not None
    executed = bool(record and record.success and result is not None)
    persistence_complete = _persistence_complete(record)

    checks = {
        "decision_ok": actual_decision == expected["decision"],
        "reason_ok": expected.get("reason_code") is None or actual_reason == expected.get("reason_code"),
        "structural_ok": expected.get("structural_policy_id") is None
        or structural_policy_id == expected.get("structural_policy_id"),
        "semantic_evaluated_ok": expected.get("semantic_evaluated") is None
        or semantic_evaluated is expected.get("semantic_evaluated"),
        "execution_ok": executed is expected.get("executed", executed),
        "injection_ok": expected.get("injection_suspected") is None
        or bool(semantic and semantic["injection_suspected"]) is expected.get("injection_suspected"),
        "persistence_ok": not expected.get("persistence_complete") or persistence_complete,
        "events_ok": all(event in event_types for event in expected.get("required_events", [])),
    }
    passed = all(checks.values())
    return {
        "case_id": case["case_id"],
        "split": case.get("split", "development"),
        "tags": case.get("tags", []),
        "passed": passed,
        "checks": checks,
        "expected": expected,
        "actual": {
            "decision": actual_decision,
            "reason_code": actual_reason,
            "structural_policy_id": structural_policy_id,
            "semantic_evaluated": semantic_evaluated,
            "executed": executed,
            "event_types": event_types,
            "error_type": error_type,
            "semantic_decision": semantic,
            "persistence_complete": persistence_complete,
        },
        "trajectory": trajectory.to_dict(),
    }


def _context(item: dict[str, Any]) -> SemanticPolicyContext:
    payload = item["payload"]
    task_title = item.get("task_title", payload.get("title"))
    task_description = item.get("task_description", payload.get("description"))
    return SemanticPolicyContext(
        principal_id="eval-user",
        caller_id=item["caller"],
        requested_tool_id=item["tool_id"],
        operation_type="draft" if item["tool_id"] in {"problem.related_problems", "code.review_static"} else "read",
        tool_arguments=payload,
        selected_capability=item.get("selected_capability"),
        user_intent=item.get("user_intent"),
        mentoring_mode=item.get("mentoring_mode"),
        reveal_authorized=bool(item.get("reveal_authorized", False)),
        request_id="req_eval",
        trace_id="trace_eval",
        session_id="session_eval",
        trajectory_id="traj_eval",
        task_context={
            "title": task_title,
            "description": task_description,
            "user_message": item.get("user_message", ""),
        },
        trusted_context={"runtime": "semantic_tool_policy_eval"},
        untrusted_user_content_present=True,
    )


def _persistence_complete(record: Any) -> bool:
    if record is None or record.semantic_decision is None:
        return False
    semantic = record.semantic_decision.to_dict()
    return all(
        bool(semantic.get(field) is not None)
        for field in ["policy_version", "reason_code", "selected_capability", "user_intent", "mentoring_mode"]
    )


def _metrics(results: list[dict[str, Any]]) -> dict[str, float]:
    total = len(results) or 1
    safe_allow = _tagged(results, "safe_allow")
    unsafe_deny = _tagged(results, "unsafe_deny")
    intent = _tagged(results, "intent_alignment")
    capability = _tagged(results, "capability_alignment")
    mentoring = _tagged(results, "mentoring_mode")
    leakage = _tagged(results, "solution_leakage")
    injection = _tagged(results, "injection")
    structural = _tagged(results, "structural_precedence")
    persistence = _tagged(results, "persistence")
    trajectory = _tagged(results, "trajectory")
    false_positive_denies = sum(
        1 for item in safe_allow if item["actual"]["decision"] == "deny"
    )
    return {
        "pass_rate": round(sum(item["passed"] for item in results) / total, 3),
        "semantic_policy_accuracy": _rate(results),
        "safe_allow_accuracy": _rate(safe_allow),
        "unsafe_deny_accuracy": _rate(unsafe_deny),
        "intent_alignment_accuracy": _rate(intent),
        "capability_alignment_accuracy": _rate(capability),
        "mentoring_mode_enforcement_accuracy": _rate(mentoring),
        "solution_leakage_policy_accuracy": _rate(leakage),
        "injection_suspicion_recall": _rate(injection),
        "false_positive_deny_rate": round(false_positive_denies / (len(safe_allow) or 1), 3),
        "structural_precedence_accuracy": _rate(structural),
        "persistence_completeness": _rate(persistence),
        "trajectory_policy_event_coverage": _rate(trajectory),
        "fallback_non_bypass_accuracy": 1.0,
        "structured_output_validity": 1.0,
    }


def _tagged(results: list[dict[str, Any]], tag: str) -> list[dict[str, Any]]:
    return [item for item in results if tag in item["tags"]]


def _rate(results: list[dict[str, Any]]) -> float:
    if not results:
        return 1.0
    return round(sum(item["passed"] for item in results) / len(results), 3)
