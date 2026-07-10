from __future__ import annotations

import time
from pathlib import Path

from app.evaluation.adapters.base import EvalAdapter, EvalAdapterConfig
from app.evaluation.code_review_eval import evaluate_code_review_cases
from app.evaluation.core.models import EvalCaseResult, EvalCheck, EvalFailure, EvalStatus, FailureCategory, EvalSuiteResult
from app.evaluation.core.thresholds import evaluate_gates


class CodeReviewEvalAdapter(EvalAdapter):
    config = EvalAdapterConfig("code_review", "code_review", Path("../evals/code_review/cases.jsonl"))

    def run(self, *, cases_path: Path | None = None, split: str | None = None) -> EvalSuiteResult:
        started = time.perf_counter()
        raw = evaluate_code_review_cases(cases_path or self.config.default_cases_path)
        results = []
        for item in raw["results"]:
            unsupported_ok = item["unsupported_claim_ok"]
            checks = [
                EvalCheck(
                    "expected_categories",
                    item["expected_ok"],
                    None if item["expected_ok"] else FailureCategory.INVALID_STRUCTURE,
                ),
                EvalCheck(
                    "forbidden_categories",
                    item["forbidden_ok"],
                    None if item["forbidden_ok"] else FailureCategory.POLICY_VIOLATION,
                ),
                EvalCheck(
                    "rewrite_policy",
                    item["rewrite_ok"],
                    None if item["rewrite_ok"] else FailureCategory.POLICY_VIOLATION,
                ),
                EvalCheck(
                    "intent_satisfaction",
                    item["intent_ok"],
                    None if item["intent_ok"] else FailureCategory.INTENT_MISMATCH,
                ),
                EvalCheck(
                    "structured_output",
                    item["structured_ok"],
                    None if item["structured_ok"] else FailureCategory.INVALID_STRUCTURE,
                ),
                EvalCheck(
                    "unsupported_claims",
                    unsupported_ok,
                    None if unsupported_ok else FailureCategory.UNSUPPORTED_CLAIM,
                ),
            ]
            failures = [EvalFailure(check.category, check.name, check.details) for check in checks if not check.passed and check.category]
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
                )
            )
        metrics = {
            "pass_rate": round(raw["passed"] / (raw["case_count"] or 1), 3),
            "workflow_precision": raw["workflow_precision"],
            "legacy_precision": raw["legacy_precision"],
            "unsupported_claim_rate": raw["unsupported_claim_rate"],
            "intent_satisfaction_rate": raw["intent_satisfaction_rate"],
            "rewrite_policy_compliance_rate": raw["rewrite_policy_compliance_rate"],
            "structured_output_validity_rate": raw["structured_output_validity_rate"],
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
            baseline_metrics={"legacy_precision": raw["legacy_precision"]},
            raw_legacy_result=raw,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )
