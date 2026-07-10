from __future__ import annotations

import time
from pathlib import Path

from app.evaluation.adapters.base import EvalAdapter, EvalAdapterConfig
from app.evaluation.adk_routing_eval import evaluate_adk_routing_cases
from app.evaluation.core.models import (
    EvalCaseResult,
    EvalCheck,
    EvalFailure,
    EvalStatus,
    FailureCategory,
    EvalSuiteResult,
)
from app.evaluation.core.thresholds import evaluate_gates


class AdkRoutingEvalAdapter(EvalAdapter):
    config = EvalAdapterConfig("adk_routing", "adk_routing", Path("../evals/adk_routing/cases.jsonl"))

    def run(self, *, cases_path: Path | None = None, split: str | None = None) -> EvalSuiteResult:
        started = time.perf_counter()
        raw = evaluate_adk_routing_cases(cases_path or self.config.default_cases_path)
        results = []
        for item in raw["results"]:
            checks = [
                EvalCheck(
                    "routing_decision",
                    item["route_ok"],
                    None if item["route_ok"] else FailureCategory.INTENT_MISMATCH,
                ),
                EvalCheck(
                    "trajectory_events",
                    item["events_ok"],
                    None if item["events_ok"] else FailureCategory.INVALID_STRUCTURE,
                ),
                EvalCheck(
                    "trajectory_identity",
                    item["identity_ok"],
                    None if item["identity_ok"] else FailureCategory.INVALID_STRUCTURE,
                ),
                EvalCheck(
                    "fallback_policy",
                    item["fallback_ok"],
                    None if item["fallback_ok"] else FailureCategory.POLICY_VIOLATION,
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
                    split="development",
                    status=EvalStatus.PASSED if not failures else EvalStatus.FAILED,
                    checks=checks,
                    failures=failures,
                    raw_result=item,
                    trace_id=item["trajectory"].get("trace_id"),
                    implementation_version="adk-routing-v1",
                )
            )
        metrics = {
            "pass_rate": round(raw["passed"] / (raw["case_count"] or 1), 3),
            "routing_accuracy": raw["routing_accuracy"],
            "trajectory_event_coverage": raw["trajectory_event_coverage"],
            "trajectory_identity_completeness": raw["trajectory_identity_completeness"],
            "fallback_policy_accuracy": raw["fallback_policy_accuracy"],
        }
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
            baseline_metrics={},
            raw_legacy_result=raw,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )
