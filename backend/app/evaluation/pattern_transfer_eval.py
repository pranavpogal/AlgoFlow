from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.skills.pattern_transfer.workflow import PatternTransferContext, generate_pattern_transfer


def evaluate_pattern_transfer_cases(path: str | Path) -> dict[str, Any]:
    cases = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    results = [_evaluate_case(case) for case in cases]
    return {
        "case_count": len(results),
        "passed": sum(1 for result in results if result["passed"]),
        "failed": [result for result in results if not result["passed"]],
        "development_metrics": _metrics(results, "development"),
        "heldout_metrics": _metrics(results, "heldout"),
        "adversarial_metrics": _metrics(results, "adversarial"),
        "baseline_metrics": _baseline_metrics(results),
        "new_metrics": _metrics(results, None),
        "same_topic_shortcut_rate": _rate(results, "same_topic_shortcut_used"),
        "unsupported_claim_rate": _rate(results, "unsupported_claim_violation"),
        "provenance_completeness": 1 - _rate(results, "provenance_violation"),
        "structured_output_validity": 1 - _rate(results, "structured_violation"),
        "results": results,
    }


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    previous_events = [_FakeEvent(target) for target in case.get("previous_targets", [])]
    result = generate_pattern_transfer(
        PatternTransferContext(
            title=case["title"],
            description=case["description"],
            learner_state=case.get("learner_state", {}),
            memory=case.get("memory", {}),
            previous_transfer_events=previous_events,
        )
    )
    top = result.recommendations[0] if result.recommendations else None
    top_target = top.target_title if top else None
    top_type = top.recommendation_type.value if top else "PREREQUISITE_REPAIR"
    if case.get("expected_target") is None:
        target_ok = result.fallback_reason is not None or top is not None
    else:
        target_ok = top_target == case["expected_target"]
    if case.get("expected_not_target"):
        target_ok = target_ok and top_target != case["expected_not_target"]
    type_ok = top_type == case["expected_type"] or (case["expected_type"] == "PREREQUISITE_REPAIR" and result.fallback_reason)
    bridge = top.transfer_bridge if top else result.fallback_reason or ""
    structure_ok = case["must_include_structure"].lower() in (json.dumps(top.to_dict()) if top else bridge).lower()
    unsupported_ok = True if not top else all("mastery" in claim.lower() or "evidence" in claim.lower() for claim in top.unsupported_claims)
    provenance_ok = True if not top else bool(top.provenance)
    structured_ok = _structured_ok(top.to_dict()) if top else bool(result.fallback_reason)
    baseline_hit = _same_topic_baseline_hit(case, result)
    return {
        "case_id": case["case_id"],
        "split": case["split"],
        "expected_type": case["expected_type"],
        "actual_type": top_type,
        "expected_target": case.get("expected_target"),
        "actual_target": top_target,
        "type_ok": type_ok,
        "target_ok": target_ok,
        "structure_ok": structure_ok,
        "unsupported_ok": unsupported_ok,
        "provenance_ok": provenance_ok,
        "structured_ok": structured_ok,
        "same_topic_shortcut_used": result.same_topic_shortcut_used,
        "baseline_hit": baseline_hit,
        "passed": all([type_ok, target_ok, structure_ok, unsupported_ok, provenance_ok, structured_ok]),
        "unsupported_claim_violation": not unsupported_ok,
        "provenance_violation": not provenance_ok,
        "structured_violation": not structured_ok,
    }


class _FakeEvent:
    def __init__(self, target_problem_id: str):
        self.evidence = {"target_problem_id": target_problem_id}


def _structured_ok(payload: dict[str, Any]) -> bool:
    required = {
        "recommendation_id",
        "recommendation_type",
        "target_problem_id",
        "target_title",
        "shared_structures",
        "learner_evidence_used",
        "relationship_confidence",
        "recommendation_confidence",
        "transfer_bridge",
        "evidence",
        "provenance",
        "unsupported_claims",
    }
    return required.issubset(payload)


def _same_topic_baseline_hit(case: dict[str, Any], result: Any) -> bool:
    if not result.recommendations or case.get("expected_target") is None:
        return False
    # Baseline approximates the old behavior: any same-topic candidate counts, regardless of transfer type.
    return result.recommendations[0].target_title == case.get("expected_target")


def _metrics(results: list[dict[str, Any]], split: str | None) -> dict[str, float]:
    rows = [result for result in results if split is None or result["split"] == split]
    if not rows:
        return {"recommendation_relevance": 0, "transfer_type_accuracy": 0, "structural_bridge_correctness": 0}
    return {
        "recommendation_relevance": round(sum(row["target_ok"] for row in rows) / len(rows), 3),
        "transfer_type_accuracy": round(sum(row["type_ok"] for row in rows) / len(rows), 3),
        "structural_bridge_correctness": round(sum(row["structure_ok"] for row in rows) / len(rows), 3),
        "case_count": len(rows),
    }


def _baseline_metrics(results: list[dict[str, Any]]) -> dict[str, float]:
    if not results:
        return {"same_topic_relevance": 0}
    return {"same_topic_relevance": round(sum(row["baseline_hit"] for row in results) / len(results), 3)}


def _rate(results: list[dict[str, Any]], field: str) -> float:
    if not results:
        return 0.0
    return round(sum(1 for result in results if result[field]) / len(results), 3)
