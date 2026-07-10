from __future__ import annotations

from typing import Any


def readiness_score(memory: dict[str, Any]) -> int:
    if "derived_learner_state" in memory:
        return int(memory["derived_learner_state"].get("readiness_score", 0))
    profile = memory.get("profile", {})
    mastery = profile.get("pattern_mastery", {})
    if not mastery:
        return 50
    base = sum(mastery.values()) / len(mastery)
    penalty = min(18, len(memory.get("mistake_counts", {})) * 3)
    activity_bonus = min(12, memory.get("attempt_count", 0) * 2)
    return max(0, min(100, round(base - penalty + activity_bonus)))


def build_weekly_plan(memory: dict[str, Any], days_remaining: int, hours_per_week: int) -> list[dict[str, Any]]:
    derived = memory.get("derived_learner_state", {})
    profile = memory.get("profile", {})
    weak_topics = derived.get("weak_topics") or profile.get("weak_topics", ["Dynamic Programming", "Graphs"])
    strong_topics = derived.get("strong_topics") or profile.get("strong_topics", [])
    weeks = max(1, round(days_remaining / 7))
    plan = []
    for week in range(1, weeks + 1):
        focus = weak_topics[(week - 1) % len(weak_topics)] if week <= max(2, weeks - 2) else "Mock Interviews"
        if week == weeks:
            focus = "Readiness Review + Mixed Mocks"
        plan.append(
            {
                "week": week,
                "focus": focus,
                "hours": hours_per_week,
                "problems": 6 if hours_per_week >= 8 else 3,
                "mentor_goal": f"Turn {focus} from recognition into confident explanation.",
                "review_loop": "Analyze -> hint-limited solve -> code review -> mistake reflection",
            }
        )
    if strong_topics:
        plan[0]["maintenance"] = f"Keep {strong_topics[0]} warm with one timed problem."
    return plan
