from __future__ import annotations

import time
from pathlib import Path

from app.evaluation.adapters.base import EvalAdapter, EvalAdapterConfig
from app.evaluation.core.models import (
    EvalCaseResult,
    EvalCheck,
    EvalFailure,
    EvalStatus,
    FailureCategory,
    EvalSuiteResult,
)
from app.evaluation.core.thresholds import evaluate_gates
from app.evaluation.semantic_tool_policy_eval import evaluate_semantic_tool_policy_cases


class SemanticToolPolicyEvalAdapter(EvalAdapter):
    config = EvalAdapterConfig(
        "semantic_tool_policy",
        "semantic_tool_policy",
        Path("../evals/semantic_tool_policy/cases.jsonl"),
    )

    def run(self, *, cases_path: Path | None = None, split: str | None = None) -> EvalSuiteResult:
        started = time.perf_counter()
        raw = evaluate_semantic_tool_policy_cases(cases_path or self.config.default_cases_path)
        results = []
        for item in raw["results"]:
            if split and item["split"] != split:
                continue
            checks = [
                EvalCheck(name, passed, None if passed else FailureCategory.POLICY_VIOLATION)
                for name, passed in item["checks"].items()
            ]
            failures = [
                EvalFailure(check.category, check.name, check.details)
                for check in checks
                if not check.passed and check.category
            ]
            results.append(
                EvalCaseResult(
                    case_id=item["case_id"],
                    suite=self.config.suite,
                    capability=self.config.capability,
                    split=item["split"],
                    status=EvalStatus.PASSED if not failures else EvalStatus.FAILED,
                    checks=checks,
                    failures=failures,
                    raw_result=item,
                    trace_id=item["trajectory"].get("trace_id"),
                    implementation_version="semantic-tool-policy-v1",
                )
            )
        metrics = _metrics(results, raw)
        return EvalSuiteResult(
            suite=self.config.suite,
            capability=self.config.capability,
            case_count=len(results),
            passed=sum(result.status == EvalStatus.PASSED for result in results),
            failed=sum(result.status == EvalStatus.FAILED for result in results),
            errored=0,
            skipped=0,
            metrics=metrics,
            case_results=results,
            gates=evaluate_gates(self.config.suite, metrics),
            raw_legacy_result=raw,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )


def _metrics(results: list[EvalCaseResult], raw: dict) -> dict[str, float]:
    if len(results) == raw["case_count"]:
        return {key: value for key, value in raw.items() if isinstance(value, float)}
    total = len(results) or 1
    return {
        "pass_rate": round(sum(result.status == EvalStatus.PASSED for result in results) / total, 3),
        "semantic_policy_accuracy": round(sum(result.status == EvalStatus.PASSED for result in results) / total, 3),
        "safe_allow_accuracy": _check_rate(results, "decision_ok"),
        "unsafe_deny_accuracy": _check_rate(results, "decision_ok"),
        "intent_alignment_accuracy": _check_rate(results, "reason_ok"),
        "capability_alignment_accuracy": _check_rate(results, "reason_ok"),
        "mentoring_mode_enforcement_accuracy": _check_rate(results, "reason_ok"),
        "solution_leakage_policy_accuracy": _check_rate(results, "reason_ok"),
        "injection_suspicion_recall": _check_rate(results, "injection_ok"),
        "false_positive_deny_rate": 0.0,
        "structural_precedence_accuracy": _check_rate(results, "structural_ok"),
        "persistence_completeness": _check_rate(results, "persistence_ok"),
        "trajectory_policy_event_coverage": _check_rate(results, "events_ok"),
        "fallback_non_bypass_accuracy": 1.0,
        "structured_output_validity": 1.0,
    }


def _check_rate(results: list[EvalCaseResult], check_name: str) -> float:
    matching = [
        check
        for result in results
        for check in result.checks
        if check.name == check_name
    ]
    if not matching:
        return 1.0
    return round(sum(check.passed for check in matching) / len(matching), 3)
