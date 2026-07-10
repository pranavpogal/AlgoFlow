from __future__ import annotations

import time
from pathlib import Path

from app.evaluation.adapters.base import EvalAdapter, EvalAdapterConfig
from app.evaluation.adk_tool_orchestration_eval import evaluate_adk_tool_orchestration_cases
from app.evaluation.core.models import (
    EvalCaseResult,
    EvalCheck,
    EvalFailure,
    EvalStatus,
    FailureCategory,
    EvalSuiteResult,
)
from app.evaluation.core.thresholds import evaluate_gates


class AdkToolOrchestrationEvalAdapter(EvalAdapter):
    config = EvalAdapterConfig(
        "adk_tool_orchestration",
        "adk_tool_orchestration",
        Path("../evals/adk_tool_orchestration/cases.jsonl"),
    )

    def run(self, *, cases_path: Path | None = None, split: str | None = None) -> EvalSuiteResult:
        started = time.perf_counter()
        raw = evaluate_adk_tool_orchestration_cases(cases_path or self.config.default_cases_path)
        results = []
        for item in raw["results"]:
            if split and item["split"] != split:
                continue
            checks = [
                EvalCheck(
                    "route_selection",
                    item["route_ok"],
                    None if item["route_ok"] else FailureCategory.INTENT_MISMATCH,
                ),
                EvalCheck(
                    "tool_request_execution",
                    item["tool_execution_ok"],
                    None if item["tool_execution_ok"] else FailureCategory.EXECUTION_ERROR,
                ),
                EvalCheck(
                    "tool_policy_enforcement",
                    item["policy_enforcement_ok"],
                    None if item["policy_enforcement_ok"] else FailureCategory.POLICY_VIOLATION,
                ),
                EvalCheck(
                    "tool_trajectory_events",
                    item["events_ok"],
                    None if item["events_ok"] else FailureCategory.INVALID_STRUCTURE,
                ),
                EvalCheck(
                    "fallback_non_bypass",
                    item["fallback_non_bypass_ok"],
                    None if item["fallback_non_bypass_ok"] else FailureCategory.POLICY_VIOLATION,
                ),
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
                    tool_calls=len(item["tool_records"]),
                    implementation_version="adk-tool-orchestration-v1",
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
        return {
            "pass_rate": round(raw["passed"] / (raw["case_count"] or 1), 3),
            "tool_request_execution_accuracy": raw["tool_request_execution_accuracy"],
            "tool_policy_enforcement_accuracy": raw["tool_policy_enforcement_accuracy"],
            "tool_trajectory_coverage": raw["tool_trajectory_coverage"],
            "tool_fallback_non_bypass_accuracy": raw["tool_fallback_non_bypass_accuracy"],
        }
    total = len(results) or 1
    return {
        "pass_rate": round(sum(result.status == EvalStatus.PASSED for result in results) / total, 3),
        "tool_request_execution_accuracy": _check_rate(results, "tool_request_execution"),
        "tool_policy_enforcement_accuracy": _check_rate(results, "tool_policy_enforcement"),
        "tool_trajectory_coverage": _check_rate(results, "tool_trajectory_events"),
        "tool_fallback_non_bypass_accuracy": _check_rate(results, "fallback_non_bypass"),
    }


def _check_rate(results: list[EvalCaseResult], check_name: str) -> float:
    checks = [check for result in results for check in result.checks if check.name == check_name]
    if not checks:
        return 1.0
    return round(sum(check.passed for check in checks) / len(checks), 3)
