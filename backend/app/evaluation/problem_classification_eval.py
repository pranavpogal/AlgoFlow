from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.skills.problem_intelligence.workflow import (
    ProblemClassificationContext,
    classify_problem,
    legacy_detect_problem_pattern,
)

LEGACY_PATTERN_TO_TOPIC = {
    "Dynamic Programming": "Dynamic Programming",
    "Graphs": "Graphs",
    "Sliding Window": "Sliding Window",
    "Binary Search": "Binary Search",
    "Trees": "Trees",
    "Backtracking": "Backtracking",
    "Greedy": "Greedy",
    "Hash Maps": "Hashing",
    "General Problem Solving": "General Problem Solving",
}

LEGACY_SUBPATTERN_TO_PATTERN = {
    "1D DP": "Decision DP",
    "LIS-style DP": "LIS-style DP",
    "Traversal": "DFS Traversal",
    "Visited-State Management": "DFS Traversal",
    "Two Pointers": "Variable-Size Window",
    "Frequency Window": "Variable-Size Window",
    "Monotonic Predicate": "Binary Search on Answer",
    "Boundary Search": "Boundary Search",
    "DFS": "Tree DFS",
    "Recursive State": "Tree DFS",
    "Choice Exploration": "Choice Exploration",
    "Pruning": "Choice Exploration",
    "Local Optimal Choice": "Greedy Sorting",
    "Exchange Argument": "Greedy Sorting",
    "Frequency Counting": "Frequency Counting",
    "Constant-Time Lookup": "Hash Lookup",
}


def evaluate_problem_classification_cases(path: str | Path) -> dict[str, Any]:
    cases = _load_cases(path)
    results = [_evaluate_case(case) for case in cases]
    failed = [result for result in results if not result["passed"]]
    return {
        "case_count": len(results),
        "passed": len(results) - len(failed),
        "failed": failed,
        "new_metrics": _metrics(results, prefix="new"),
        "baseline_metrics": _metrics(results, prefix="legacy"),
        "unsupported_claim_rate": _rate(results, "unsupported_claim_violation"),
        "provenance_completeness_rate": 1 - _rate(results, "provenance_violation"),
        "structured_output_validity_rate": 1 - _rate(results, "structured_violation"),
        "calibration_findings": _calibration_findings(results),
        "results": results,
    }


def _load_cases(path: str | Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    result = classify_problem(
        ProblemClassificationContext(
            title=case["title"],
            description=case["description"],
            problem_number=case.get("problem_number"),
            known_tags=case.get("known_tags", []),
        )
    )
    legacy = legacy_detect_problem_pattern(case["title"], case["description"])
    legacy_pattern = _legacy_primary_pattern(legacy)
    expected_secondary = set(case.get("expected_secondary_topics", []))
    new_secondary = set(result.secondary_topics)
    max_confidence = case.get("max_confidence")

    primary_topic_ok = result.primary_topic == case["expected_primary_topic"]
    primary_pattern_ok = result.primary_pattern == case["expected_primary_pattern"]
    secondary_ok = expected_secondary.issubset(new_secondary)
    provenance_ok = bool(result.provenance) and all(item.provenance.value for item in result.evidence)
    structured_ok = _structured_ok(result.to_legacy_dict())
    unsupported_ok = all("mastery" not in claim.lower() or "does not imply" in claim.lower() for claim in result.unsupported_claims)
    confidence_ok = max_confidence is None or result.confidence <= max_confidence

    return {
        "case_id": case["case_id"],
        "expected_primary_topic": case["expected_primary_topic"],
        "expected_primary_pattern": case["expected_primary_pattern"],
        "expected_secondary_topics": sorted(expected_secondary),
        "new_primary_topic": result.primary_topic,
        "new_primary_pattern": result.primary_pattern,
        "new_secondary_topics": sorted(new_secondary),
        "new_confidence": result.confidence,
        "max_confidence": max_confidence,
        "legacy_primary_topic": LEGACY_PATTERN_TO_TOPIC.get(legacy["pattern"], legacy["pattern"]),
        "legacy_primary_pattern": legacy_pattern,
        "primary_topic_ok": primary_topic_ok,
        "primary_pattern_ok": primary_pattern_ok,
        "secondary_ok": secondary_ok,
        "confidence_ok": confidence_ok,
        "provenance_ok": provenance_ok,
        "structured_ok": structured_ok,
        "unsupported_ok": unsupported_ok,
        "passed": all([primary_topic_ok, primary_pattern_ok, secondary_ok, confidence_ok, provenance_ok, structured_ok, unsupported_ok]),
        "unsupported_claim_violation": not unsupported_ok,
        "provenance_violation": not provenance_ok,
        "structured_violation": not structured_ok,
    }


def _legacy_primary_pattern(legacy: dict[str, Any]) -> str:
    for subpattern in legacy.get("sub_patterns", []):
        if subpattern in LEGACY_SUBPATTERN_TO_PATTERN:
            return LEGACY_SUBPATTERN_TO_PATTERN[subpattern]
    return legacy.get("pattern", "General Problem Solving")


def _structured_ok(payload: dict[str, Any]) -> bool:
    required = {
        "primary_topic",
        "secondary_topics",
        "primary_pattern",
        "structural_cues",
        "prerequisites",
        "related_patterns",
        "difficulty_signals",
        "confidence",
        "evidence",
        "provenance",
        "unsupported_claims",
        "taxonomy_version",
    }
    if not required.issubset(payload):
        return False
    return all(
        {"observed_evidence", "inferred_label", "confidence", "provenance", "cue_type"}.issubset(item)
        for item in payload["evidence"]
    )


def _metrics(results: list[dict[str, Any]], *, prefix: str) -> dict[str, float]:
    topic_hits = sum(1 for result in results if result[f"{prefix}_primary_topic"] == result["expected_primary_topic"])
    pattern_hits = sum(1 for result in results if result[f"{prefix}_primary_pattern"] == result["expected_primary_pattern"])
    secondary_precision, secondary_recall = _secondary_metrics(results, prefix)
    total = len(results) or 1
    return {
        "primary_topic_accuracy": round(topic_hits / total, 3),
        "pattern_precision": round(pattern_hits / total, 3),
        "pattern_recall": round(pattern_hits / total, 3),
        "multi_label_precision": secondary_precision,
        "multi_label_recall": secondary_recall,
    }


def _secondary_metrics(results: list[dict[str, Any]], prefix: str) -> tuple[float, float]:
    predicted_total = 0
    expected_total = 0
    hits = 0
    for result in results:
        expected = set(result["expected_secondary_topics"])
        predicted = set(result.get(f"{prefix}_secondary_topics", [])) if prefix == "new" else set()
        predicted_total += len(predicted)
        expected_total += len(expected)
        hits += len(expected & predicted)
    precision = round(hits / predicted_total, 3) if predicted_total else 0.0
    recall = round(hits / expected_total, 3) if expected_total else 1.0
    return precision, recall


def _calibration_findings(results: list[dict[str, Any]]) -> dict[str, Any]:
    ambiguous = [result for result in results if result.get("max_confidence") is not None]
    overconfident = [result["case_id"] for result in ambiguous if result["new_confidence"] > 0.82]
    return {
        "ambiguous_case_count": len(ambiguous),
        "overconfident_ambiguous_cases": overconfident,
    }


def _rate(results: list[dict[str, Any]], field: str) -> float:
    if not results:
        return 0.0
    return round(sum(1 for result in results if result[field]) / len(results), 3)
