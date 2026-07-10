import pytest
from httpx import ASGITransport, AsyncClient

from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal
from app.main import app
from app.memory.repository import learning_events_for_user
from app.skills.problem_intelligence.workflow import ProblemClassificationContext, classify_problem


@pytest.fixture(autouse=True)
async def sync_test_schema():
    await init_db()


def test_curated_problem_returns_high_confidence_typed_taxonomy():
    result = classify_problem(
        ProblemClassificationContext(
            title="Largest Divisible Subset",
            description="Given positive integers, return largest subset where each pair is divisible.",
        )
    )

    assert result.primary_topic == "Dynamic Programming"
    assert result.primary_pattern == "LIS-style DP"
    assert result.confidence >= 0.9
    assert "CURATED_METADATA" in [item.value for item in result.provenance]
    assert "Sorting" in result.prerequisites
    assert result.taxonomy_version


def test_ambiguous_problem_preserves_secondary_topic_and_uncertainty():
    result = classify_problem(
        ProblemClassificationContext(
            title="Minimum Size Subarray Sum",
            description=(
                "Find the minimum length contiguous subarray whose sum is at least target; "
                "positive numbers make a sliding window possible but binary search on answer can also work."
            ),
        )
    )

    assert result.primary_topic == "Sliding Window"
    assert result.primary_pattern == "Variable-Size Window"
    assert "Binary Search" in result.secondary_topics
    assert result.confidence <= 0.82


def test_fallback_is_low_confidence_and_does_not_overclaim():
    result = classify_problem(ProblemClassificationContext(title="Custom Puzzle", description="Return the desired output."))

    assert result.primary_topic == "General Problem Solving"
    assert result.confidence == 0.35
    assert any("Insufficient structural evidence" in claim for claim in result.unsupported_claims)


@pytest.mark.asyncio
async def test_problem_analysis_api_returns_evidence_and_classification_events():
    user_id = "phase-4c-classification-user"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/problems/analyze",
            headers={"x-user-id": user_id},
            json={
                "problem_number": "368",
                "title": "Largest Divisible Subset",
                "description": "Given positive integers, return largest subset where every pair is divisible.",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["pattern"] == "Dynamic Programming"
    assert payload["primary_pattern"] == "LIS-style DP"
    assert payload["confidence"] >= 0.9
    assert payload["evidence"]
    assert payload["unsupported_claims"]

    async with AsyncSessionLocal() as session:
        events = await learning_events_for_user(session, user_id, limit=20)

    event_types = {event.event_type for event in events}
    assert "ProblemClassified" in event_types
    assert "PatternDetected" in event_types
    assert "StructuralCueDetected" in event_types
    classified = next(event for event in events if event.event_type == "ProblemClassified")
    assert classified.evidence["mastery_evidence"] is False
    assert classified.evidence["classification_only"] is True
