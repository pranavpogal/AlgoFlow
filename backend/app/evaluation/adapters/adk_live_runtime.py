from __future__ import annotations

import time
from pathlib import Path

from app.evaluation.adapters.base import EvalAdapter, EvalAdapterConfig
from app.evaluation.adk_live_runtime_eval import evaluate_adk_live_runtime_cases
from app.evaluation.core.models import (
    EvalCaseResult,
    EvalCheck,
    EvalFailure,
    EvalStatus,
    FailureCategory,
    EvalSuiteResult,
)
from app.evaluation.core.thresholds import evaluate_gates


class AdkLiveRuntimeEvalAdapter(EvalAdapter):
    config = EvalAdapterConfig(
        "adk_live_runtime",
        "adk_live_runtime",
        Path("../evals/adk_live_runtime/cases.jsonl"),
    )

    def run(self, *, cases_path: Path | None = None, split: str | None = None) -> EvalSuiteResult:
        started = time.perf_counter()
        raw = evaluate_adk_live_runtime_cases(cases_path or self.config.default_cases_path)
        results = []
        for item in raw["results"]:
            if split and item["split"] != split:
                continue
            checks = [
                EvalCheck(
                    "routing_parity",
                    item["route_ok"],
                    None if item["route_ok"] else FailureCategory.INTENT_MISMATCH,
                ),
                EvalCheck(
                    "runtime_mode",
                    item["runtime_ok"],
                    None if item["runtime_ok"] else FailureCategory.POLICY_VIOLATION,
                ),
                EvalCheck(
                    "fallback_policy",
                    item["fallback_ok"],
                    None if item["fallback_ok"] else FailureCategory.POLICY_VIOLATION,
                ),
                EvalCheck(
                    "trajectory_events",
                    item["events_ok"],
                    None if item["events_ok"] else FailureCategory.INVALID_STRUCTURE,
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
                    implementation_version="adk-live-runtime-v1",
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
            "live_boundary_accuracy": raw["live_boundary_accuracy"],
            "live_fallback_accuracy": raw["live_fallback_accuracy"],
            "trajectory_event_coverage": raw["trajectory_event_coverage"],
            "deterministic_parity_accuracy": raw["deterministic_parity_accuracy"],
        }
    total = len(results) or 1
    return {
        "pass_rate": round(sum(result.status == EvalStatus.PASSED for result in results) / total, 3),
        "live_boundary_accuracy": _check_rate(results, "runtime_mode"),
        "live_fallback_accuracy": _check_rate(results, "fallback_policy"),
        "trajectory_event_coverage": _check_rate(results, "trajectory_events"),
        "deterministic_parity_accuracy": _check_rate(results, "routing_parity"),
    }


def _check_rate(results: list[EvalCaseResult], check_name: str) -> float:
    checks = [check for result in results for check in result.checks if check.name == check_name]
    if not checks:
        return 1.0
    return round(sum(check.passed for check in checks) / len(checks), 3)
