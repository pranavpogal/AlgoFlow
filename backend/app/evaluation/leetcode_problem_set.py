from __future__ import annotations

from pathlib import Path
from typing import Any

from app.skills.problem_intelligence.workflow import ProblemClassificationContext, classify_problem


CASE_KEYS = {
    "problem_number",
    "title",
    "difficulty",
    "description",
    "expected_topic",
    "expected_pattern",
    "expected_sub_patterns",
    "expected_prerequisites",
    "notes",
}


def evaluate_leetcode_problem_set(path: str | Path, *, use_problem_number: bool = True) -> dict[str, Any]:
    cases = load_leetcode_markdown_cases(path)
    results = [_evaluate_case(case, use_problem_number=use_problem_number) for case in cases]
    failed = [result for result in results if not result["passed"]]
    return {
        "case_count": len(results),
        "passed": len(results) - len(failed),
        "failed": failed,
        "metrics": _metrics(results),
        "results": results,
    }


def load_leetcode_markdown_cases(path: str | Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                cases.append(_normalize_case(current))
                current = {}
            continue
        key, separator, value = line.partition(":")
        if separator and key in CASE_KEYS:
            current[key] = value.strip()
    if current:
        cases.append(_normalize_case(current))
    return cases


def _normalize_case(case: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(case)
    normalized["expected_sub_patterns"] = _split_csv(normalized.get("expected_sub_patterns", ""))
    normalized["expected_prerequisites"] = _split_csv(normalized.get("expected_prerequisites", ""))
    return normalized


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _evaluate_case(case: dict[str, Any], *, use_problem_number: bool) -> dict[str, Any]:
    result = classify_problem(
        ProblemClassificationContext(
            title=case["title"],
            description=case["description"],
            problem_number=case.get("problem_number") if use_problem_number else None,
            use_canonical_title_catalog=True,
        )
    )
    expected_subpatterns = set(case["expected_sub_patterns"])
    expected_prerequisites = set(case["expected_prerequisites"])
    observed_subpatterns = set(result.subpatterns)
    observed_prerequisites = set(result.prerequisites)
    checks = {
        "difficulty": result.difficulty == case["difficulty"],
        "topic": result.primary_topic == case["expected_topic"],
        "pattern": result.primary_pattern == case["expected_pattern"],
        "subpatterns": expected_subpatterns.issubset(observed_subpatterns),
        "prerequisites": expected_prerequisites.issubset(observed_prerequisites),
        "provenance": "CURATED_METADATA" in {item.value for item in result.provenance},
        "confidence": result.confidence >= 0.9,
    }
    return {
        "case_id": f"leetcode_{case['problem_number']}",
        "title": case["title"],
        "expected": {
            "difficulty": case["difficulty"],
            "topic": case["expected_topic"],
            "pattern": case["expected_pattern"],
            "sub_patterns": sorted(expected_subpatterns),
            "prerequisites": sorted(expected_prerequisites),
        },
        "observed": {
            "difficulty": result.difficulty,
            "topic": result.primary_topic,
            "pattern": result.primary_pattern,
            "sub_patterns": result.subpatterns,
            "prerequisites": result.prerequisites,
            "confidence": result.confidence,
            "provenance": [item.value for item in result.provenance],
        },
        "checks": checks,
        "passed": all(checks.values()),
    }


def _metrics(results: list[dict[str, Any]]) -> dict[str, float]:
    total = len(results) or 1
    check_names = ["difficulty", "topic", "pattern", "subpatterns", "prerequisites", "provenance", "confidence"]
    return {
        f"{name}_accuracy": round(sum(1 for result in results if result["checks"][name]) / total, 3)
        for name in check_names
    }
