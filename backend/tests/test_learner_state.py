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
