from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.skills.code_review.workflow import CodeReviewContext, review_code_workflow
from app.tools.code_review import review_code_heuristics

LEGACY_CATEGORY_MAP = {
    "Off-by-one / boundary handling": "boundary",
    "DP initialization clarity": "dp_base_case",
    "Binary search boundary reasoning": "binary_search_invariant",
    "Graph visitation update timing": "graph_visitation",
}


def evaluate_code_review_cases(path: str | Path) -> dict[str, Any]:
    cases = _load_cases(path)
    results = [_evaluate_case(case) for case in cases]
    failures = [result for result in results if not result["passed"]]
    workflow_precision = _precision(results, "workflow")
    legacy_precision = _precision(results, "legacy")
    return {
        "case_count": len(results),
        "passed": len(results) - len(failures),
        "failed": failures,
        "workflow_precision": workflow_precision,
        "legacy_precision": legacy_precision,
        "unsupported_claim_rate": _rate(results, "unsupported_claim_violation"),
        "intent_satisfaction_rate": 1 - _rate(results, "intent_violation"),
        "rewrite_policy_compliance_rate": 1 - _rate(results, "rewrite_violation"),
        "structured_output_validity_rate": 1 - _rate(results, "structured_violation"),
        "results": results,
    }


def _load_cases(path: str | Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    workflow = review_code_workflow(
        CodeReviewContext(
            title=case["title"],
            language=case["language"],
            code=case["code"],
            user_intent=case.get("user_intent"),
            learner_state={},
        )
    )
    workflow_categories = {finding.category.value for finding in workflow.findings}
    expected = set(case.get("expected_categories", []))
    forbidden = set(case.get("forbidden_categories", []))
    legacy_categories = _legacy_categories(case)

    expected_ok = expected.issubset(workflow_categories)
    forbidden_ok = workflow_categories.isdisjoint(forbidden)
    rewrite_ok = bool(workflow.corrected_code) == bool(case.get("rewrite_expected", False))
    summary_required = case.get("summary_must_include")
    intent_ok = not summary_required or summary_required.lower() in workflow.senior_engineer_summary.lower()
    structured_ok = all(_finding_is_structured(finding.to_dict()) for finding in workflow.findings)
    unsupported_claim_ok = _unsupported_claim_ok(workflow.language_supported, workflow.unsupported_claims)

    return {
        "case_id": case["case_id"],
        "workflow_categories": sorted(workflow_categories),
        "legacy_categories": sorted(legacy_categories),
        "expected_categories": sorted(expected),
        "forbidden_categories": sorted(forbidden),
        "expected_ok": expected_ok,
        "forbidden_ok": forbidden_ok,
        "rewrite_ok": rewrite_ok,
        "intent_ok": intent_ok,
        "structured_ok": structured_ok,
        "unsupported_claim_ok": unsupported_claim_ok,
        "workflow": {
            "intent": workflow.intent.value,
            "language_supported": workflow.language_supported,
            "analysis_layers": workflow.analysis_layers,
            "finding_count": len(workflow.findings),
            "rewrite_allowed": workflow.rewrite_allowed,
        },
        "legacy": {"finding_count": len(legacy_categories)},
        "passed": all([expected_ok, forbidden_ok, rewrite_ok, intent_ok, structured_ok, unsupported_claim_ok]),
        "unsupported_claim_violation": not unsupported_claim_ok,
        "intent_violation": not intent_ok,
        "rewrite_violation": not rewrite_ok,
        "structured_violation": not structured_ok,
    }


def _legacy_categories(case: dict[str, Any]) -> set[str]:
    result = review_code_heuristics(case["language"], case["code"])
    return {LEGACY_CATEGORY_MAP[mistake] for mistake in result.get("suspected_mistakes", []) if mistake in LEGACY_CATEGORY_MAP}


def _finding_is_structured(finding: dict[str, Any]) -> bool:
    required = {
        "finding_id",
        "category",
        "severity",
        "confidence",
        "evidence_type",
        "evidence",
        "location",
        "message",
        "pedagogical_action",
        "provenance",
    }
    return required.issubset(finding) and isinstance(finding["location"], dict)


def _unsupported_claim_ok(language_supported: bool, unsupported_claims: list[str]) -> bool:
    if language_supported:
        return any("No learner code was executed" in claim for claim in unsupported_claims)
    return any("No AST-backed" in claim for claim in unsupported_claims) and any(
        "No learner code was executed" in claim for claim in unsupported_claims
    )


def _precision(results: list[dict[str, Any]], key: str) -> float:
    true_positive = 0
    predicted = 0
    for result in results:
        categories = set(result[f"{key}_categories"])
        expected = set(result["expected_categories"])
        forbidden = set(result["forbidden_categories"])
        if not categories:
            continue
        predicted += len(categories)
        true_positive += len(categories & expected)
        true_positive -= len(categories & forbidden)
    if predicted <= 0:
        return 0.0
    return round(max(true_positive, 0) / predicted, 3)


def _rate(results: list[dict[str, Any]], field: str) -> float:
    if not results:
        return 0.0
    return round(sum(1 for result in results if result[field]) / len(results), 3)
