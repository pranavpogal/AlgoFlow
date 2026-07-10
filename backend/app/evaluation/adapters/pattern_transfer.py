from __future__ import annotations

import time
from pathlib import Path

from app.evaluation.adapters.base import EvalAdapter, EvalAdapterConfig
from app.evaluation.core.models import EvalCaseResult, EvalCheck, EvalFailure, EvalStatus, FailureCategory, EvalSuiteResult
from app.evaluation.core.thresholds import evaluate_gates
from app.evaluation.pattern_transfer_eval import evaluate_pattern_transfer_cases


class PatternTransferEvalAdapter(EvalAdapter):
    config = EvalAdapterConfig("pattern_transfer", "pattern_transfer", Path("../evals/pattern_transfer/cases.jsonl"))

    def run(self, *, cases_path: Path | None = None, split: str | None = None) -> EvalSuiteResult:
        started = time.perf_counter()
        raw = evaluate_pattern_transfer_cases(cases_path or self.config.default_cases_path)
        results = []
        for item in raw["results"]:
            if split and item["split"] != split:
                continue
            shortcut_ok = not item["same_topic_shortcut_used"]
            checks = [
                EvalCheck(
                    "transfer_type",
                    item["type_ok"],
                    None if item["type_ok"] else FailureCategory.WRONG_TRANSFER_TYPE,
                ),
                EvalCheck(
                    "target_relevance",
                    item["target_ok"],
                    None if item["target_ok"] else FailureCategory.INVALID_STRUCTURE,
                ),
                EvalCheck(
                    "structural_bridge",
                    item["structure_ok"],
                    None if item["structure_ok"] else FailureCategory.INVALID_STRUCTURE,
                ),
                EvalCheck(
                    "unsupported_claims",
                    item["unsupported_ok"],
                    None if item["unsupported_ok"] else FailureCategory.UNSUPPORTED_CLAIM,
                ),
                EvalCheck(
                    "provenance",
                    item["provenance_ok"],
                    None if item["provenance_ok"] else FailureCategory.MISSING_PROVENANCE,
                ),
                EvalCheck(
                    "structured_output",
                    item["structured_ok"],
                    None if item["structured_ok"] else FailureCategory.INVALID_STRUCTURE,
                ),
                EvalCheck(
                    "same_topic_shortcut",
                    shortcut_ok,
                    None if shortcut_ok else FailureCategory.POLICY_VIOLATION,
                ),
            ]
            failures = [EvalFailure(check.category, check.name, check.details) for check in checks if not check.passed and check.category]
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
                )
            )
        filtered_metrics = _metrics_from_results(results)
        metrics = {
            "pass_rate": round(sum(r.status == EvalStatus.PASSED for r in results) / (len(results) or 1), 3),
            **filtered_metrics,
            "development_recommendation_relevance": raw["development_metrics"]["recommendation_relevance"],
            "heldout_recommendation_relevance": raw["heldout_metrics"]["recommendation_relevance"],
            "adversarial_recommendation_relevance": raw["adversarial_metrics"]["recommendation_relevance"],
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
            baseline_metrics=raw["baseline_metrics"],
            raw_legacy_result=raw,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )


def _metrics_from_results(results: list[EvalCaseResult]) -> dict[str, float]:
    if not results:
        return {
            "recommendation_relevance": 0.0,
            "transfer_type_accuracy": 0.0,
            "structural_bridge_correctness": 0.0,
            "case_count": 0,
            "same_topic_shortcut_rate": 0.0,
            "unsupported_claim_rate": 0.0,
            "provenance_completeness": 0.0,
            "structured_output_validity": 0.0,
        }
    rows = [result.raw_result for result in results]
    return {
        "recommendation_relevance": round(sum(row["target_ok"] for row in rows) / len(rows), 3),
        "transfer_type_accuracy": round(sum(row["type_ok"] for row in rows) / len(rows), 3),
        "structural_bridge_correctness": round(sum(row["structure_ok"] for row in rows) / len(rows), 3),
        "case_count": len(rows),
        "same_topic_shortcut_rate": round(sum(row["same_topic_shortcut_used"] for row in rows) / len(rows), 3),
        "unsupported_claim_rate": round(sum(row["unsupported_claim_violation"] for row in rows) / len(rows), 3),
        "provenance_completeness": round(1 - (sum(row["provenance_violation"] for row in rows) / len(rows)), 3),
        "structured_output_validity": round(1 - (sum(row["structured_violation"] for row in rows) / len(rows)), 3),
    }
