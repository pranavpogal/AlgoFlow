from __future__ import annotations

import json
import time
from pathlib import Path

from app.evaluation.adapters.base import EvalAdapter, EvalAdapterConfig
from app.evaluation.core.models import EvalCaseResult, EvalCheck, EvalFailure, EvalStatus, FailureCategory, EvalSuiteResult
from app.evaluation.core.thresholds import evaluate_gates
from app.evaluation.hint_eval import evaluate_hint_cases


class HintingEvalAdapter(EvalAdapter):
    config = EvalAdapterConfig("hinting", "progressive_hinting", Path("../evals/hint_leakage/cases.jsonl"))

    def run(self, *, cases_path: Path | None = None, split: str | None = None) -> EvalSuiteResult:
        started = time.perf_counter()
        path = cases_path or self.config.default_cases_path
        raw = evaluate_hint_cases(path)
        raw_cases = _load_cases(path)
        case_by_id = {case["case_id"]: case for case in raw_cases}
        results = []
        for item in raw["results"]:
            case = case_by_id.get(item["case_id"], {})
            case_split = case.get("split", "development")
            if split and case_split != split:
                continue
            checks = [
                EvalCheck("intervention_type", item["intervention_ok"], None if item["intervention_ok"] else FailureCategory.INTENT_MISMATCH),
                EvalCheck("solution_leakage", item["leakage_ok"], None if item["leakage_ok"] else FailureCategory.SOLUTION_LEAKAGE, {"forbidden_hits": item.get("forbidden_hits", [])}),
            ]
            failures = [
                EvalFailure(check.category, check.name, check.details)
                for check in checks
                if not check.passed and check.category is not None
            ]
            status = EvalStatus.PASSED if not failures else EvalStatus.FAILED
            results.append(
                EvalCaseResult(
                    case_id=item["case_id"],
                    suite=self.config.suite,
                    capability=self.config.capability,
                    split=case_split,
                    status=status,
                    metrics={"intervention_ok": float(item["intervention_ok"]), "leakage_ok": float(item["leakage_ok"])},
                    checks=checks,
                    failures=failures,
                    raw_result=item,
                )
            )
        metrics = _metrics(results)
        return EvalSuiteResult(
            suite=self.config.suite,
            capability=self.config.capability,
            case_count=len(results),
            passed=sum(result.status == EvalStatus.PASSED for result in results),
            failed=sum(result.status == EvalStatus.FAILED for result in results),
            errored=sum(result.status == EvalStatus.ERROR for result in results),
            skipped=sum(result.status == EvalStatus.SKIPPED for result in results),
            metrics=metrics,
            case_results=results,
            gates=evaluate_gates(self.config.suite, metrics),
            raw_legacy_result=raw,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )


def _load_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _metrics(results: list[EvalCaseResult]) -> dict[str, float]:
    total = len(results) or 1
    intervention = sum(result.metrics.get("intervention_ok", 0) for result in results) / total
    leakage_failures = sum(1 for result in results if any(f.category == FailureCategory.SOLUTION_LEAKAGE for f in result.failures))
    return {
        "pass_rate": round(sum(result.status == EvalStatus.PASSED for result in results) / total, 3),
        "intervention_type_accuracy": round(intervention, 3),
        "solution_leakage_rate": round(leakage_failures / total, 3),
    }
