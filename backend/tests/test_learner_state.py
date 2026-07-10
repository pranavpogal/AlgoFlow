import pytest
from httpx import ASGITransport, AsyncClient

from app.memory.learner_state import derive_learner_state
from app.main import app


def test_new_user_state_has_unknown_confidence_and_no_fake_topics():
    state = derive_learner_state(
        {
            "attempt_count": 0,
            "learning_event_count": 0,
            "pattern_counts": {},
            "mistake_counts": {},
        }
    )

    assert state["readiness_score"] == 0
    assert state["confidence"] == "unknown"
    assert state["strong_topics"] == []
    assert state["weak_topics"] == []
    assert state["topic_mastery"] == []


def test_repeated_mistakes_create_weak_topic_with_evidence():
    state = derive_learner_state(
        {
            "attempt_count": 3,
            "learning_event_count": 6,
            "pattern_counts": {"Dynamic Programming": 3},
            "mistake_counts": {"DP initialization clarity": 3},
        }
    )

    dp = next(item for item in state["topic_mastery"] if item["topic"] == "Dynamic Programming")
    assert dp["evidence_count"] == 6
    assert dp["negative_evidence_count"] == 3
    assert "Dynamic Programming" in state["weak_topics"]
    assert state["confidence"] in {"medium", "high"}


def test_learner_state_exposes_velocity_risk_and_next_actions():
    state = derive_learner_state(
        {
            "attempt_count": 2,
            "learning_event_counts": {
                "CodeSubmitted": 2,
                "MisconceptionDetected": 2,
                "AnalyticsViewed": 10,
            },
            "pattern_counts": {"Dynamic Programming": 2},
            "mistake_counts": {"DP transition mistake": 3},
            "attempt_history": [
                {
                    "title": "House Robber",
                    "pattern": "Dynamic Programming",
                    "created_at": "2026-07-01T10:00:00",
                },
                {
                    "title": "Delete and Earn",
                    "pattern": "Dynamic Programming",
                    "created_at": "2026-07-03T10:00:00",
                },
            ],
            "event_history": [
                {
                    "event_type": "MisconceptionDetected",
                    "concept": "DP transition mistake",
                    "created_at": "2026-07-03T10:10:00",
                },
                {
                    "event_type": "AnalyticsViewed",
                    "created_at": "2026-07-03T10:20:00",
                },
            ],
            "interview_summaries": [
                {
                    "session_id": "interview-1",
                    "turn_count": 3,
                    "total_score": 10,
                    "max_score": 25,
                    "rubric_scores": {
                        "communication": 3,
                        "correctness": 2,
                        "complexity": 1,
                        "testing": 1,
                        "adaptability": 3,
                    },
                    "updated_at": "2026-07-04T10:00:00",
                }
            ],
        }
    )

    assert state["evidence_count"] == 9
    assert state["evidence_summary"]["active_event_count"] == 1
    assert state["readiness_components"]["interview"] == 40
    assert state["learning_velocity"][0]["activity_count"] == 3
    assert state["mistake_trends"][0]["risk"] in {"medium", "high"}
    assert state["interview_readiness"]["rubric_strengths"] == ["communication", "adaptability"]
    assert any(action["source"] == "topic_mastery" for action in state["next_best_actions"])


@pytest.mark.asyncio
async def test_analytics_for_new_user_does_not_claim_default_strengths():
    user_id = "new-analytics-user-no-evidence"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(f"/api/v1/analytics/{user_id}", headers={"x-user-id": user_id})

    body = response.json()
    assert response.status_code == 200
    assert body["confidence"] == "unknown"
    assert body["strongest_topics"] == []
    assert body["weakest_topics"] == []
    assert body["evidence_count"] == 0
    assert body["evidence_summary"]["attempt_count"] == 0
    assert body["readiness_components"]["mastery"] == 0
    assert body["learning_velocity"] == []
    assert body["next_best_actions"][0]["source"] == "learner_state"
