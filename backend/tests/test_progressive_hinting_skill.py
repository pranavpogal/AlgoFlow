import pytest
from httpx import ASGITransport, AsyncClient
from uuid import uuid4

from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal
from app.main import app
from app.memory.repository import learning_events_for_user
from app.skills.progressive_hinting.workflow import (
    HintContext,
    HintIntent,
    InterventionType,
    detect_intent,
    generate_progressive_hint,
)


@pytest.fixture(autouse=True)
async def sync_test_schema():
    await init_db()


def test_detects_idea_validation_intent():
    assert detect_intent("Am I thinking correctly if I use rob or skip choices?", False) is HintIntent.IDEA_VALIDATION


def test_no_solution_request_does_not_reveal_recurrence():
    result = generate_progressive_hint(
        HintContext(
            title="House Robber",
            description="Find max without adjacent houses.",
            pattern="Dynamic Programming",
            difficulty="Medium",
            current_hint_level=0,
            user_attempt="Give me one hint, don't give the solution.",
            reveal_solution=False,
            learner_state={"confidence": "unknown", "weak_topics": []},
            previous_hint_events=[],
        )
    )

    assert result.intervention_type is InterventionType.STATE_DEFINITION_PROMPT
    assert result.reveals_solution is False
    assert "dp[i-1]" not in result.hint
    assert "return" not in result.hint.lower()


def test_wrong_dp_state_gets_misconception_correction():
    result = generate_progressive_hint(
        HintContext(
            title="House Robber",
            description="Find max without adjacent houses.",
            pattern="Dynamic Programming",
            difficulty="Medium",
            current_hint_level=1,
            user_attempt="I think dp[i] stores whether I robbed house i.",
            reveal_solution=False,
            learner_state={"confidence": "low", "weak_topics": ["Dynamic Programming"]},
            previous_hint_events=[],
        )
    )

    assert result.intervention_type is InterventionType.MISCONCEPTION_CORRECTION
    assert result.detected_misconception == "State stores action instead of optimal value"
    assert result.reveals_solution is False


@pytest.mark.asyncio
async def test_hint_api_records_structured_hint_events_and_avoids_repeating_intervention():
    user_id = f"progressive-hint-api-user-{uuid4().hex}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        first = await client.post(
            "/api/v1/hints/next",
            headers={"x-user-id": user_id},
            json={
                "title": "House Robber",
                "description": "Find maximum amount without robbing adjacent houses.",
                "current_hint_level": 0,
                "user_attempt": "Give me one hint, don't give the solution.",
            },
        )
        second = await client.post(
            "/api/v1/hints/next",
            headers={"x-user-id": user_id},
            json={
                "title": "House Robber",
                "description": "Find maximum amount without robbing adjacent houses.",
                "current_hint_level": first.json()["level"],
                "user_attempt": "Another hint please, still no solution.",
            },
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["reveals_solution"] is False
    assert second.json()["reveals_solution"] is False
    assert first.json()["hint"] != second.json()["hint"]

    async with AsyncSessionLocal() as session:
        delivered = await learning_events_for_user(session, user_id, event_type="HintDelivered", limit=10)
        requested = await learning_events_for_user(session, user_id, event_type="HintRequested", limit=10)

    assert len(delivered) >= 2
    assert len(requested) >= 2
    interventions = [event.evidence["intervention_type"] for event in delivered[:2]]
    assert len(set(interventions)) == 2
    assert delivered[0].evidence["solution_leakage_risk"] == "low"


@pytest.mark.asyncio
async def test_explicit_solution_request_can_reveal_solution_level_hint():
    user_id = "progressive-hint-solution-user"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/hints/next",
            headers={"x-user-id": user_id},
            json={
                "title": "House Robber",
                "description": "Find maximum amount without robbing adjacent houses.",
                "current_hint_level": 3,
                "user_attempt": "Give me the full solution now.",
                "reveal_solution": True,
            },
        )

    assert response.status_code == 200
    assert response.json()["reveals_solution"] is True
    assert response.json()["level"] == 5
