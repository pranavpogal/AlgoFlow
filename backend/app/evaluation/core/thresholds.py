from __future__ import annotations

from dataclasses import dataclass
from operator import ge, le
from typing import Any

from app.evaluation.core.models import GateResult


@dataclass(frozen=True)
class GatePolicy:
    metric: str
    operator: str
    threshold: float
    severity: str = "blocking"

    def evaluate(self, metrics: dict[str, Any]) -> GateResult:
        actual = _lookup_metric(metrics, self.metric)
        if actual is None:
            return GateResult(self.metric, self.operator, self.threshold, None, self.severity, False, "metric missing")
        op = {">=": ge, "<=": le}.get(self.operator)
        if op is None:
            return GateResult(self.metric, self.operator, self.threshold, actual, self.severity, False, "unsupported operator")
        passed = bool(op(float(actual), self.threshold))
        message = f"{actual} {self.operator} {self.threshold}"
        return GateResult(self.metric, self.operator, self.threshold, float(actual), self.severity, passed, message)


GATE_POLICIES = {
    "adk_live_runtime": [
        GatePolicy("live_boundary_accuracy", ">=", 1.0, "blocking"),
        GatePolicy("live_fallback_accuracy", ">=", 1.0, "blocking"),
        GatePolicy("trajectory_event_coverage", ">=", 1.0, "blocking"),
        GatePolicy("deterministic_parity_accuracy", ">=", 1.0, "blocking"),
    ],
    "adk_tool_orchestration": [
        GatePolicy("tool_request_execution_accuracy", ">=", 1.0, "blocking"),
        GatePolicy("tool_policy_enforcement_accuracy", ">=", 1.0, "blocking"),
        GatePolicy("tool_trajectory_coverage", ">=", 1.0, "blocking"),
        GatePolicy("tool_fallback_non_bypass_accuracy", ">=", 1.0, "blocking"),
    ],
    "adk_routing": [
        GatePolicy("routing_accuracy", ">=", 1.0, "blocking"),
        GatePolicy("trajectory_event_coverage", ">=", 1.0, "blocking"),
        GatePolicy("trajectory_identity_completeness", ">=", 1.0, "blocking"),
        GatePolicy("fallback_policy_accuracy", ">=", 1.0, "blocking"),
    ],
    "hinting": [
        GatePolicy("solution_leakage_rate", "<=", 0.0, "blocking"),
        GatePolicy("intervention_type_accuracy", ">=", 1.0, "blocking"),
    ],
    "code_review": [
        GatePolicy("unsupported_claim_rate", "<=", 0.0, "blocking"),
        GatePolicy("rewrite_policy_compliance_rate", ">=", 1.0, "blocking"),
        GatePolicy("structured_output_validity_rate", ">=", 1.0, "blocking"),
    ],
    "problem_intelligence": [
        GatePolicy("unsupported_claim_rate", "<=", 0.0, "blocking"),
        GatePolicy("structured_output_validity_rate", ">=", 1.0, "blocking"),
        GatePolicy("provenance_completeness", ">=", 1.0, "blocking"),
    ],
    "pattern_transfer": [
        GatePolicy("same_topic_shortcut_rate", "<=", 0.0, "blocking"),
        GatePolicy("unsupported_claim_rate", "<=", 0.0, "blocking"),
        GatePolicy("provenance_completeness", ">=", 1.0, "blocking"),
    ],
    "semantic_tool_policy": [
        GatePolicy("semantic_policy_accuracy", ">=", 1.0, "blocking"),
        GatePolicy("structural_precedence_accuracy", ">=", 1.0, "blocking"),
        GatePolicy("solution_leakage_policy_accuracy", ">=", 1.0, "blocking"),
        GatePolicy("fallback_non_bypass_accuracy", ">=", 1.0, "blocking"),
        GatePolicy("false_positive_deny_rate", "<=", 0.0, "blocking"),
    ],
}


def evaluate_gates(suite: str, metrics: dict[str, Any]) -> list[GateResult]:
    return [policy.evaluate(metrics) for policy in GATE_POLICIES.get(suite, [])]


def _lookup_metric(metrics: dict[str, Any], metric: str) -> float | None:
    value = metrics.get(metric)
    if isinstance(value, (int, float)):
        return float(value)
    return None
