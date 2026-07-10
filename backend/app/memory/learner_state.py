from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

MIN_EVIDENCE_FOR_CONFIDENT_TOPIC = 3
PASSIVE_EVENT_TYPES = {"AnalyticsViewed"}


def derive_learner_state(memory: dict[str, Any]) -> dict[str, Any]:
    """Derive an evidence-backed learner state from stored attempts, mistakes, and events.

    This intentionally stays simple: it reports confidence and evidence counts rather than
    pretending to know true mastery from sparse data.
    """
    pattern_counts: dict[str, int] = memory.get("pattern_counts", {})
    mistake_counts: dict[str, int] = memory.get("mistake_counts", {})
    learning_event_counts: dict[str, int] = memory.get("learning_event_counts", {})
    if learning_event_counts:
        learning_event_count = sum(
            count
            for event_type, count in learning_event_counts.items()
            if event_type not in PASSIVE_EVENT_TYPES
        )
    else:
        learning_event_count = int(memory.get("learning_event_count", 0))
    attempt_count = int(memory.get("attempt_count", 0))

    topic_evidence = _topic_evidence(pattern_counts, mistake_counts)
    strong_topics = [
        item["topic"]
        for item in topic_evidence
        if item["confidence"] in {"medium", "high"} and item["score"] >= 70
    ]
    weak_topics = [
        item["topic"]
        for item in topic_evidence
        if item["evidence_count"] >= 1 and item["score"] <= 45
    ]

    readiness = _readiness_score(topic_evidence, attempt_count, mistake_counts)
    evidence_count = attempt_count + learning_event_count + sum(mistake_counts.values())
    confidence = _overall_confidence(evidence_count)

    return {
        "readiness_score": readiness,
        "confidence": confidence,
        "evidence_count": evidence_count,
        "strong_topics": strong_topics,
        "weak_topics": weak_topics,
        "topic_mastery": topic_evidence,
        "common_mistakes": [
            {
                "category": category,
                "count": count,
                "confidence": _mistake_confidence(count),
                "evidence": f"Observed {count} time(s) in reviews/events.",
            }
            for category, count in sorted(mistake_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        "recommendations": _recommendations(strong_topics, weak_topics, mistake_counts, confidence),
        "evidence_summary": {
            "attempt_count": attempt_count,
            "learning_event_count": learning_event_count,
            "mistake_evidence_count": sum(mistake_counts.values()),
        },
    }


def _topic_evidence(pattern_counts: dict[str, int], mistake_counts: dict[str, int]) -> list[dict[str, Any]]:
    mistake_by_topic = _mistakes_by_topic(mistake_counts)
    topics = set(pattern_counts) | set(mistake_by_topic)
    rows: list[dict[str, Any]] = []
    for topic in sorted(topics):
        positive = pattern_counts.get(topic, 0)
        negative = mistake_by_topic.get(topic, 0)
        evidence_count = positive + negative
        score = _topic_score(positive, negative)
        rows.append(
            {
                "topic": topic,
                "score": score,
                "confidence": _topic_confidence(evidence_count),
                "evidence_count": evidence_count,
                "positive_evidence_count": positive,
                "negative_evidence_count": negative,
                "explanation": _topic_explanation(topic, positive, negative, score),
            }
        )
    return sorted(rows, key=lambda row: (row["score"], row["evidence_count"]), reverse=True)


def _mistakes_by_topic(mistake_counts: dict[str, int]) -> dict[str, int]:
    grouped: dict[str, int] = defaultdict(int)
    for category, count in mistake_counts.items():
        lowered = category.lower()
        if "dp" in lowered or "dynamic" in lowered:
            grouped["Dynamic Programming"] += count
        elif "graph" in lowered:
            grouped["Graphs"] += count
        elif "binary" in lowered:
            grouped["Binary Search"] += count
        elif "off-by-one" in lowered or "boundary" in lowered:
            grouped["Boundary Reasoning"] += count
        else:
            grouped["General Debugging"] += count
    return dict(grouped)


def _topic_score(positive: int, negative: int) -> int:
    if positive + negative == 0:
        return 0
    base = 50 + positive * 12 - negative * 15
    return max(0, min(100, base))


def _topic_confidence(evidence_count: int) -> str:
    if evidence_count >= MIN_EVIDENCE_FOR_CONFIDENT_TOPIC * 2:
        return "high"
    if evidence_count >= MIN_EVIDENCE_FOR_CONFIDENT_TOPIC:
        return "medium"
    if evidence_count > 0:
        return "low"
    return "unknown"


def _overall_confidence(evidence_count: int) -> str:
    if evidence_count >= 20:
        return "high"
    if evidence_count >= 8:
        return "medium"
    if evidence_count > 0:
        return "low"
    return "unknown"


def _mistake_confidence(count: int) -> str:
    if count >= 5:
        return "high"
    if count >= 2:
        return "medium"
    return "low"


def _readiness_score(topic_evidence: list[dict[str, Any]], attempt_count: int, mistake_counts: dict[str, int]) -> int:
    if not topic_evidence and attempt_count == 0:
        return 0
    if topic_evidence:
        weighted = sum(row["score"] * max(row["evidence_count"], 1) for row in topic_evidence)
        total_weight = sum(max(row["evidence_count"], 1) for row in topic_evidence)
        base = weighted / total_weight
    else:
        base = 40
    activity_bonus = min(10, attempt_count * 2)
    mistake_penalty = min(20, sum(mistake_counts.values()) * 3)
    return max(0, min(100, round(base + activity_bonus - mistake_penalty)))


def _topic_explanation(topic: str, positive: int, negative: int, score: int) -> str:
    if positive + negative == 0:
        return f"No evidence yet for {topic}."
    return (
        f"Score {score} is based on {positive} positive pattern exposure(s) "
        f"and {negative} related mistake signal(s)."
    )


def _recommendations(
    strong_topics: list[str], weak_topics: list[str], mistake_counts: dict[str, int], confidence: str
) -> list[str]:
    if confidence == "unknown":
        return ["Solve or analyze a few problems so AlgoFlow can build an evidence-backed profile."]
    recommendations: list[str] = []
    if weak_topics:
        recommendations.append(f"Prioritize targeted practice for {weak_topics[0]} with hint limits.")
    if mistake_counts:
        top_mistake = Counter(mistake_counts).most_common(1)[0][0]
        recommendations.append(f"Review recent {top_mistake} mistakes before starting the next problem.")
    if strong_topics:
        recommendations.append(f"Maintain {strong_topics[0]} with one timed mixed-review problem.")
    return recommendations or ["Continue building evidence with reviewed solves and mock interview turns."]
