from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.skills.progressive_hinting.workflow import HintContext, generate_progressive_hint

FORBIDDEN_SOLUTION_MARKERS = [
    "dp[i-1]",
    "dp[i - 1]",
    "nums[i] + dp[i-2]",
    "return dp",
    "def ",
]


def evaluate_hint_cases(path: str | Path) -> dict[str, Any]:
    cases = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    for case in cases:
        payload = case["input"]
        previous_interventions = payload.get("previous_interventions", [])
        previous_events = [_FakeEvent(intervention) for intervention in previous_interventions]
        result = generate_progressive_hint(
            HintContext(
                title=payload["title"],
                description=payload["description"],
                pattern=_pattern_for(payload["title"], payload["description"]),
                difficulty="Unknown",
                current_hint_level=payload.get("current_hint_level", 0),
                user_attempt=payload.get("user_attempt"),
                reveal_solution=payload.get("reveal_solution", False),
                learner_state={"confidence": "unknown", "weak_topics": []},
                previous_hint_events=previous_events,
            )
        )
        forbidden_hits = [marker for marker in FORBIDDEN_SOLUTION_MARKERS if marker.lower() in result.hint.lower()]
        expected_intervention = case.get("expected_intervention")
        intervention_ok = not expected_intervention or result.intervention_type.value == expected_intervention
        leakage_ok = not forbidden_hits or result.reveals_solution
        results.append(
            {
                "case_id": case["case_id"],
                "intervention": result.intervention_type.value,
                "expected_intervention": expected_intervention,
                "intervention_ok": intervention_ok,
                "leakage_ok": leakage_ok,
                "forbidden_hits": forbidden_hits,
            }
        )
    return {
        "case_count": len(results),
        "passed": sum(1 for item in results if item["intervention_ok"] and item["leakage_ok"]),
        "failed": [item for item in results if not (item["intervention_ok"] and item["leakage_ok"])],
        "results": results,
    }


class _FakeEvent:
    def __init__(self, intervention: str) -> None:
        self.evidence = {"intervention_type": intervention}


def _pattern_for(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    if "rob" in text or "dp" in text or "divisible" in text:
        return "Dynamic Programming"
    if "graph" in text or "node" in text:
        return "Graphs"
    if "binary" in text or "search" in text:
        return "Binary Search"
    if "greedy" in text:
        return "Greedy"
    return "General Problem Solving"
