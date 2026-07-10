from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

MIN_EVIDENCE_FOR_CONFIDENT_TOPIC = 3
PASSIVE_EVENT_TYPES = {"AnalyticsViewed", "MemoryRetrieved"}


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
    event_history = _active_event_history(memory.get("event_history", []))
    attempt_history = memory.get("attempt_history", [])
    interview_summaries = memory.get("interview_summaries", [])

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

    velocity = _learning_velocity(attempt_history, event_history)
    interview_summary = _interview_readiness(interview_summaries)
    readiness_components = _readiness_components(
        topic_evidence,
        attempt_count,
        mistake_counts,
        velocity,
        interview_summary,
    )
    readiness = _readiness_score(readiness_components)
    evidence_count = attempt_count + learning_event_count + sum(mistake_counts.values())
    confidence = _overall_confidence(evidence_count)
    mistake_trends = _mistake_trends(mistake_counts, event_history)
    topic_risk = _topic_risk(topic_evidence)

    return {
        "readiness_score": readiness,
        "readiness_components": readiness_components,
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
        "mistake_trends": mistake_trends,
        "topic_risk": topic_risk,
        "learning_velocity": velocity,
        "interview_readiness": interview_summary,
        "next_best_actions": _next_best_actions(
            strong_topics,
            weak_topics,
            mistake_counts,
            mistake_trends,
            velocity,
            interview_summary,
            confidence,
        ),
        "recommendations": _recommendations(strong_topics, weak_topics, mistake_counts, confidence),
        "evidence_summary": {
            "attempt_count": attempt_count,
            "learning_event_count": learning_event_count,
            "mistake_evidence_count": sum(mistake_counts.values()),
            "active_event_count": len(event_history),
            "interview_session_count": len(interview_summaries),
        },
        "limitations": _limitations(confidence, interview_summary),
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
                "risk": _risk_label(score, evidence_count),
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


def _readiness_components(
    topic_evidence: list[dict[str, Any]],
    attempt_count: int,
    mistake_counts: dict[str, int],
    velocity: list[dict[str, Any]],
    interview_summary: dict[str, Any],
) -> dict[str, Any]:
    if topic_evidence:
        weighted = sum(row["score"] * max(row["evidence_count"], 1) for row in topic_evidence)
        total_weight = sum(max(row["evidence_count"], 1) for row in topic_evidence)
        mastery = round(weighted / total_weight)
    else:
        mastery = 0 if attempt_count == 0 else 40
    consistency = min(100, attempt_count * 12 + sum(bucket["activity_count"] for bucket in velocity[-4:]) * 4)
    mistake_penalty = min(40, sum(mistake_counts.values()) * 5)
    interview = int(interview_summary.get("score_percent", 0))
    return {
        "mastery": mastery,
        "consistency": consistency,
        "mistake_penalty": mistake_penalty,
        "interview": interview,
        "weights": {
            "mastery": 0.5,
            "consistency": 0.2,
            "interview": 0.2,
            "mistake_penalty": -0.1,
        },
        "explanation": (
            "Readiness blends topic mastery, recent consistency, mock-interview rubric evidence, "
            "and a bounded repeated-mistake penalty."
        ),
    }


def _readiness_score(components: dict[str, Any]) -> int:
    mastery = int(components.get("mastery", 0))
    consistency = int(components.get("consistency", 0))
    interview = int(components.get("interview", 0))
    mistake_penalty = int(components.get("mistake_penalty", 0))
    if mastery == 0 and consistency == 0 and interview == 0:
        return 0
    score = mastery * 0.5 + consistency * 0.2 + interview * 0.2 - mistake_penalty * 0.1
    return max(0, min(100, round(score)))


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


def _active_event_history(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in events if event.get("event_type") not in PASSIVE_EVENT_TYPES]


def _learning_velocity(attempts: list[dict[str, Any]], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for attempt in attempts:
        label = _week_label(attempt.get("created_at"))
        bucket = buckets.setdefault(label, _empty_velocity_bucket(label))
        bucket["attempt_count"] += 1
        bucket["activity_count"] += 1
        if attempt.get("pattern"):
            bucket["patterns"].append(attempt["pattern"])
    for event in events:
        label = _week_label(event.get("created_at"))
        bucket = buckets.setdefault(label, _empty_velocity_bucket(label))
        bucket["event_count"] += 1
        bucket["activity_count"] += 1
        if event.get("event_type") == "MisconceptionDetected":
            bucket["mistake_signal_count"] += 1
    rows = []
    for label in sorted(buckets)[-6:]:
        bucket = buckets[label]
        patterns = Counter(bucket.pop("patterns")).most_common(2)
        bucket["top_patterns"] = [pattern for pattern, _ in patterns]
        bucket["trend"] = _velocity_trend(bucket)
        rows.append(bucket)
    return rows


def _empty_velocity_bucket(label: str) -> dict[str, Any]:
    return {
        "week": label,
        "activity_count": 0,
        "attempt_count": 0,
        "event_count": 0,
        "mistake_signal_count": 0,
        "patterns": [],
    }


def _week_label(value: str | None) -> str:
    if not value:
        return "unknown-week"
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return "unknown-week"
    year, week, _ = parsed.isocalendar()
    return f"{year}-W{week:02d}"


def _velocity_trend(bucket: dict[str, Any]) -> str:
    if bucket["activity_count"] >= 8:
        return "high_activity"
    if bucket["activity_count"] >= 3:
        return "steady"
    if bucket["activity_count"] > 0:
        return "light"
    return "none"


def _interview_readiness(interviews: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [item for item in interviews if item.get("max_score")]
    if not scored:
        return {
            "session_count": len(interviews),
            "score_percent": 0,
            "confidence": "unknown",
            "summary": "No scored mock-interview evidence yet.",
            "rubric_strengths": [],
            "rubric_weaknesses": [],
        }
    latest = sorted(scored, key=lambda item: item.get("updated_at") or item.get("created_at") or "")[-1]
    total = int(latest.get("total_score", 0))
    max_score = max(1, int(latest.get("max_score", 1)))
    percent = round(total / max_score * 100)
    rubric = {key: int(value) for key, value in (latest.get("rubric_scores") or {}).items()}
    strengths = [key for key, value in sorted(rubric.items(), key=lambda item: item[1], reverse=True) if value >= 3]
    weaknesses = [key for key, value in sorted(rubric.items(), key=lambda item: item[1]) if value <= 1]
    return {
        "session_count": len(scored),
        "latest_session_id": latest.get("session_id"),
        "latest_persona": latest.get("persona"),
        "latest_problem_title": latest.get("problem_title"),
        "turn_count": latest.get("turn_count", 0),
        "score_percent": percent,
        "confidence": _topic_confidence(int(latest.get("turn_count", 0))),
        "rubric_strengths": strengths[:3],
        "rubric_weaknesses": weaknesses[:3],
        "summary": f"Latest mock interview scored {total}/{max_score} across {latest.get('turn_count', 0)} turn(s).",
    }


def _mistake_trends(mistake_counts: dict[str, int], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recent_concepts = Counter(
        event.get("concept")
        for event in events[-30:]
        if event.get("event_type") in {"MisconceptionDetected", "MisconceptionAddressed"} and event.get("concept")
    )
    rows = []
    for category, count in sorted(mistake_counts.items(), key=lambda item: item[1], reverse=True):
        recent = recent_concepts.get(category, 0)
        rows.append(
            {
                "category": category,
                "count": count,
                "recent_count": recent,
                "risk": _mistake_risk(count, recent),
                "trend": "active" if recent else "historical",
            }
        )
    return rows


def _mistake_risk(total: int, recent: int) -> str:
    if total >= 5 or recent >= 3:
        return "high"
    if total >= 2 or recent >= 1:
        return "medium"
    return "low"


def _topic_risk(topic_evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "topic": item["topic"],
            "risk": item["risk"],
            "score": item["score"],
            "evidence_count": item["evidence_count"],
            "reason": item["explanation"],
        }
        for item in topic_evidence
    ]


def _risk_label(score: int, evidence_count: int) -> str:
    if evidence_count == 0:
        return "unknown"
    if score <= 35:
        return "high"
    if score <= 60:
        return "medium"
    return "low"


def _next_best_actions(
    strong_topics: list[str],
    weak_topics: list[str],
    mistake_counts: dict[str, int],
    mistake_trends: list[dict[str, Any]],
    velocity: list[dict[str, Any]],
    interview_summary: dict[str, Any],
    confidence: str,
) -> list[dict[str, Any]]:
    if confidence == "unknown":
        return [
            {
                "action": "Create baseline evidence",
                "why": "No meaningful learner evidence exists yet.",
                "priority": "high",
                "source": "learner_state",
            }
        ]
    actions: list[dict[str, Any]] = []
    if weak_topics:
        actions.append(
            {
                "action": f"Run a focused drill on {weak_topics[0]}",
                "why": "This topic has the lowest evidence-backed mastery score.",
                "priority": "high",
                "source": "topic_mastery",
            }
        )
    high_risk = next((item for item in mistake_trends if item["risk"] == "high"), None)
    if high_risk:
        actions.append(
            {
                "action": f"Review {high_risk['category']} before the next timed solve",
                "why": "Repeated mistake evidence suggests this is still active.",
                "priority": "high",
                "source": "mistake_trends",
            }
        )
    if interview_summary.get("score_percent", 0) < 60:
        actions.append(
            {
                "action": "Complete a scored mock interview turn",
                "why": "Interview communication evidence is sparse or below target.",
                "priority": "medium",
                "source": "interview_readiness",
            }
        )
    if velocity and velocity[-1]["activity_count"] <= 2:
        actions.append(
            {
                "action": "Schedule two short practice sessions this week",
                "why": "Recent activity is light, so consistency is limiting readiness.",
                "priority": "medium",
                "source": "learning_velocity",
            }
        )
    if strong_topics:
        actions.append(
            {
                "action": f"Maintain {strong_topics[0]} with one mixed review problem",
                "why": "Strong topics decay without spaced retrieval.",
                "priority": "low",
                "source": "topic_mastery",
            }
        )
    if not mistake_counts and not actions:
        actions.append(
            {
                "action": "Submit one solution for review",
                "why": "Reviewed code provides stronger evidence than analysis alone.",
                "priority": "medium",
                "source": "evidence_quality",
            }
        )
    return actions[:4]


def _limitations(confidence: str, interview_summary: dict[str, Any]) -> list[str]:
    limitations = [
        "Analytics are deterministic and evidence-derived; they are not a guarantee of interview performance.",
        "Problem exposure and recommendations do not count as mastery by themselves.",
    ]
    if confidence in {"unknown", "low"}:
        limitations.append("Learner confidence is sparse, so topic and readiness signals should be treated cautiously.")
    if interview_summary.get("confidence") in {"unknown", "low"}:
        limitations.append("Mock-interview readiness is limited until several scored turns exist.")
    return limitations
