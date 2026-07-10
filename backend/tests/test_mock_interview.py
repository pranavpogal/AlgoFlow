from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.base import InterviewSession
from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal
from app.main import app


@pytest.fixture(autouse=True)
async def sync_test_schema():
    await init_db()


@pytest.mark.asyncio
async def test_mock_interview_persists_transcript_and_scorecard_across_turns() -> None:
    user_id = f"interview-user-{uuid4().hex}"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        first = await client.post(
            "/api/v1/mock-interview/turn",
            headers={"x-user-id": user_id},
            json={
                "persona": "Google",
                "problem_title": "House Robber",
                "message": "My approach uses DP state to track the best value after each house.",
            },
        )
        first_body = first.json()
        second = await client.post(
            "/api/v1/mock-interview/turn",
            headers={"x-user-id": user_id},
            json={
                "session_id": first_body["session_id"],
                "persona": "Google",
                "problem_title": "House Robber",
                "message": "The time complexity is O(n), space can be O(1), and I would test empty and single input.",
            },
        )

    second_body = second.json()
    assert first.status_code == 200
    assert second.status_code == 200
    assert first_body["turn_index"] == 1
    assert second_body["turn_index"] == 2
    assert second_body["rubric_scores"]["complexity"] >= 1
    assert second_body["rubric_scores"]["testing"] >= 1
    assert second_body["scorecard"]["turn_count"] == 2
    assert second_body["evaluation_summary"].startswith("Rubric total")

    async with AsyncSessionLocal() as session:
        interview = await session.get(InterviewSession, first_body["session_id"])

    assert interview is not None
    assert interview.user_id == user_id
    assert len(interview.transcript) == 4
    assert interview.scorecard["turn_count"] == 2


@pytest.mark.asyncio
async def test_mock_interview_persona_changes_interviewer_style() -> None:
    user_id = f"interview-persona-{uuid4().hex}"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/mock-interview/turn",
            headers={"x-user-id": user_id},
            json={
                "persona": "Amazon",
                "problem_title": "LRU Cache",
                "message": "I would use a hash map and linked list and discuss tradeoffs.",
            },
        )

    body = response.json()
    assert response.status_code == 200
    assert "Amazon-style" in body["interviewer_message"]
    assert body["persona_style"].startswith("Amazon-style")
    assert body["rubric_scores"]["adaptability"] >= 1


@pytest.mark.asyncio
async def test_mock_interview_session_is_user_scoped() -> None:
    session_id = f"shared-session-{uuid4().hex}"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        first = await client.post(
            "/api/v1/mock-interview/turn",
            headers={"x-user-id": "owner-user"},
            json={
                "session_id": session_id,
                "persona": "Meta",
                "problem_title": "Two Sum",
                "message": "I would use a hash map and explain the invariant.",
            },
        )
        second = await client.post(
            "/api/v1/mock-interview/turn",
            headers={"x-user-id": "other-user"},
            json={
                "session_id": session_id,
                "persona": "Meta",
                "problem_title": "Two Sum",
                "message": "Trying to continue someone else's session.",
            },
        )

    assert first.status_code == 200
    assert second.status_code == 403
    assert second.json()["error"]["code"] == "FORBIDDEN"

    async with AsyncSessionLocal() as session:
        rows = (await session.execute(select(InterviewSession).where(InterviewSession.id == session_id))).scalars().all()

    assert len(rows) == 1
    assert rows[0].user_id == "owner-user"
