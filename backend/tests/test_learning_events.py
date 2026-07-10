import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import AsyncSessionLocal
from app.db.init_db import init_db
from app.main import app
from app.memory.repository import learning_events_for_user


@pytest.fixture(autouse=True)
async def sync_test_schema():
    await init_db()


@pytest.mark.asyncio
async def test_problem_analysis_records_classification_event_for_resolved_user():
    user_id = "event-analysis-user"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/problems/analyze",
            headers={"x-user-id": user_id},
            json={
                "user_id": "spoofed-event-user",
                "problem_number": "368",
                "title": "Largest Divisible Subset",
                "description": "Given positive integers, return the largest subset where pairs are divisible.",
            },
        )

    assert response.status_code == 200
    async with AsyncSessionLocal() as session:
        events = await learning_events_for_user(session, user_id, event_type="ProblemClassified")

    assert events
    event = events[0]
    assert event.user_id == user_id
    assert event.problem_title == "Largest Divisible Subset"
    assert event.concept == "Dynamic Programming"
    assert event.evidence["problem_number"] == "368"


@pytest.mark.asyncio
async def test_code_review_records_submission_review_and_misconception_events_without_full_code():
    user_id = "event-review-user"
    code = "def rob(nums):\n    dp = [0] * len(nums)\n    for i in range(len(nums)):\n        dp[i] = dp[i-1]\n    return dp[-1]"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/code-review",
            headers={"x-user-id": user_id},
            json={"title": "House Robber", "language": "Python", "code": code},
        )

    assert response.status_code == 200
    async with AsyncSessionLocal() as session:
        events = await learning_events_for_user(session, user_id, limit=10)

    event_types = {event.event_type for event in events}
    assert "CodeSubmitted" in event_types
    assert "ReviewDelivered" in event_types
    assert "MisconceptionDetected" in event_types

    submission = next(event for event in events if event.event_type == "CodeSubmitted")
    assert submission.evidence["code_length"] == len(code)
    assert code not in str(submission.evidence)


@pytest.mark.asyncio
async def test_hint_and_interview_events_are_user_scoped():
    user_id = "event-session-user"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        hint_response = await client.post(
            "/api/v1/hints/next",
            headers={"x-user-id": user_id},
            json={
                "title": "House Robber",
                "description": "Find max money without adjacent houses.",
                "current_hint_level": 0,
            },
        )
        interview_response = await client.post(
            "/api/v1/mock-interview/turn",
            headers={"x-user-id": user_id},
            json={"persona": "Google", "problem_title": "House Robber", "message": "My approach uses dp."},
        )

    assert hint_response.status_code == 200
    assert interview_response.status_code == 200
    async with AsyncSessionLocal() as session:
        user_events = await learning_events_for_user(session, user_id, limit=20)
        other_events = await learning_events_for_user(session, "not-the-user", limit=20)

    assert {"HintDelivered", "InterviewAnswerSubmitted"}.issubset(
        {event.event_type for event in user_events}
    )
    assert other_events == []
