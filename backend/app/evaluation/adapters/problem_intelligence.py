from __future__ import annotations

import time
from pathlib import Path

from app.evaluation.adapters.base import EvalAdapter, EvalAdapterConfig
from app.evaluation.core.models import EvalCaseResult, EvalCheck, EvalFailure, EvalStatus, FailureCategory, EvalSuiteResult
from app.evaluation.core.thresholds import evaluate_gates
from app.evaluation.problem_classification_eval import evaluate_problem_classification_cases


class ProblemIntelligenceEvalAdapter(EvalAdapter):
    config = EvalAdapterConfig("problem_intelligence", "problem_intelligence", Path("../evals/problem_classification/cases.jsonl"))

    def run(self, *, cases_path: Path | None = None, split: str | None = None) -> EvalSuiteResult:
        started = time.perf_counter()
        raw = evaluate_problem_classification_cases(cases_path or self.config.default_cases_path)
        results = []
        for item in raw["results"]:
            checks = [
                EvalCheck("primary_topic", item["primary_topic_ok"], None if item["primary_topic_ok"] else FailureCategory.WRONG_CLASSIFICATION),
                EvalCheck("primary_pattern", item["primary_pattern_ok"], None if item["primary_pattern_ok"] else FailureCategory.WRONG_CLASSIFICATION),
                EvalCheck("secondary_topics", item["secondary_ok"], None if item["secondary_ok"] else FailureCategory.WRONG_CLASSIFICATION),
                EvalCheck("confidence", item["confidence_ok"], None if item["confidence_ok"] else FailureCategory.METRIC_FAILURE),
                EvalCheck("provenance", item["provenance_ok"], None if item["provenance_ok"] else FailureCategory.MISSING_PROVENANCE),
                EvalCheck("structured_output", item["structured_ok"], None if item["structured_ok"] else FailureCategory.INVALID_STRUCTURE),
                EvalCheck("unsupported_claims", item["unsupported_ok"], None if item["unsupported_ok"] else FailureCategory.UNSUPPORTED_CLAIM),
            ]
            failures = [EvalFailure(check.category, check.name, check.details) for check in checks if not check.passed and check.category]
            results.append(EvalCaseResult(item["case_id"], self.config.suite, self.config.capability, "development", EvalStatus.PASSED if not failures else EvalStatus.FAILED, checks=checks, failures=failures, raw_result=item))
        metrics = {
            "pass_rate": round(raw["passed"] / (raw["case_count"] or 1), 3),
            **raw["new_metrics"],
            "unsupported_claim_rate": raw["unsupported_claim_rate"],
            "provenance_completeness": raw["provenance_completeness_rate"],
            "structured_output_validity_rate": raw["structured_output_validity_rate"],
        }
        return EvalSuiteResult(self.config.suite, self.config.capability, len(results), sum(r.status == EvalStatus.PASSED for r in results), sum(r.status == EvalStatus.FAILED for r in results), 0, 0, metrics, results, evaluate_gates(self.config.suite, metrics), raw["baseline_metrics"], raw, round((time.perf_counter() - started) * 1000, 2))
