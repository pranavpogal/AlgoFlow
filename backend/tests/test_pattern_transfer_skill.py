import pytest
from httpx import ASGITransport, AsyncClient
from uuid import uuid4

from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal
from app.main import app
from app.memory.repository import learning_events_for_user
from app.skills.pattern_transfer.workflow import PatternTransferContext, TransferType, generate_pattern_transfer


@pytest.fixture(autouse=True)
async def sync_test_schema():
    await init_db()


def test_transfer_uses_structural_bridge_not_topic_shortcut():
    result = generate_pattern_transfer(
        PatternTransferContext(
            title="Capacity To Ship Packages Within D Days",
            description="minimum capacity monotonic predicate feasibility binary search on answer",
            learner_state={"confidence": "high"},
            memory={
                "pattern_counts": {"Binary Search": 6},
                "mistake_counts": {},
                "learning_event_counts": {"CodeReviewCompleted": 3},
            },
        )
    )

    top = result.recommendations[0]
    assert top.target_title == "Koko Eating Bananas"
    assert top.recommendation_type == TransferType.FAR_TRANSFER
    assert "Binary Search on Answer" in top.shared_structures
    assert result.same_topic_shortcut_used is False
    assert "CURATED_TRANSFER_RELATION" in top.provenance


def test_unknown_learner_state_stays_cautious():
    result = generate_pattern_transfer(
        PatternTransferContext(
            title="Partition Equal Subset Sum",
            description="choose items target sum capacity subset sum knapsack dp",
            learner_state={"confidence": "unknown"},
            memory={"pattern_counts": {}, "mistake_counts": {}, "learning_event_counts": {}},
        )
    )

    top = result.recommendations[0]
    assert top.recommendation_type == TransferType.PREREQUISITE_REPAIR
    assert top.learner_state_confidence < 0.5
    assert any("Insufficient evidence" in claim for claim in top.unsupported_claims)


def test_repeated_recommendation_is_avoided():
    class Event:
        evidence = {"target_problem_id": "lc_213"}

    result = generate_pattern_transfer(
        PatternTransferContext(
            title="House Robber",
            description="maximum amount without adjacent houses rob skip decision dp",
            learner_state={"confidence": "medium"},
            memory={
                "pattern_counts": {"Dynamic Programming": 3},
                "mistake_counts": {},
                "learning_event_counts": {"ReviewDelivered": 2},
            },
            previous_transfer_events=[Event()],
        )
    )

    assert result.recommendations[0].target_title != "House Robber II"


@pytest.mark.asyncio
async def test_pattern_transfer_api_records_recommendation_events():
    user_id = f"phase-4d-transfer-user-{uuid4().hex}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/pattern-transfer",
            headers={"x-user-id": user_id},
            json={
                "title": "House Robber",
                "description": "maximum amount without adjacent houses rob skip decision dp",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendations"]
    assert payload["same_topic_shortcut_used"] is False
    assert payload["transfer_taxonomy"]

    async with AsyncSessionLocal() as session:
        events = await learning_events_for_user(session, user_id, limit=20)

    event_types = {event.event_type for event in events}
    assert "PatternTransferRequested" in event_types
    assert "PatternTransferRecommended" in event_types
    recommendation = next(event for event in events if event.event_type == "PatternTransferRecommended")
    assert recommendation.evidence["mastery_evidence"] is False
    assert recommendation.evidence["target_problem_id"]
