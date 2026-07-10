from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from uuid import uuid4

from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal
from app.main import app
from app.memory.context import build_memory_context
from app.memory.repository import learning_events_for_user
from app.memory.vector_store import vector_memory


class FakeVectorStore:
    def __init__(self) -> None:
        self.rows = {
            "user-a": [
                {
                    "id": "mem-a-1",
                    "text": "Previously struggled with DP base cases on House Robber.",
                    "metadata": {"type": "code_review", "problem": "House Robber"},
                    "score": 3,
                }
            ],
            "user-b": [
                {
                    "id": "mem-b-1",
                    "text": "Other user struggled with graph visitation.",
                    "metadata": {"type": "hint", "problem": "Number of Islands"},
                    "score": 3,
                }
            ],
        }

    def search(self, user_id: str, query: str, limit: int = 5):
        return self.rows.get(user_id, [])[:limit]


def test_memory_context_is_same_user_scoped_and_provenance_bearing() -> None:
    context = build_memory_context(
        principal_user_id="user-a",
        target_user_id="user-a",
        query="House Robber DP base case",
        purpose="hint_personalization",
        store=FakeVectorStore(),
    )

    assert context.applied is True
    assert context.policy_decision.policy_id == "memory.read.same_user.allowed"
    assert context.retrieved[0].memory_id == "mem-a-1"
    assert context.retrieved[0].provenance["source"] == "vector_memory.search"
    assert "Other user" not in context.snippets()[0]


def test_memory_context_denies_cross_user_access() -> None:
    context = build_memory_context(
        principal_user_id="user-a",
        target_user_id="user-b",
        query="graph visitation",
        purpose="hint_personalization",
        store=FakeVectorStore(),
    )

    assert context.applied is False
    assert context.retrieved == []
    assert context.policy_decision.policy_id == "memory.same_user_required"


@pytest.mark.asyncio
async def test_hint_endpoint_applies_retrieved_memory_with_provenance() -> None:
    await init_db()
    user_id = f"rag-hint-user-{uuid4().hex}"
    vector_memory.add(
        user_id,
        "Previously struggled with DP base cases on House Robber.",
        {"type": "code_review", "problem": "House Robber", "pattern": "Dynamic Programming"},
    )
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/hints/next",
            headers={"x-user-id": user_id},
            json={
                "title": "House Robber",
                "description": "Find maximum amount without robbing adjacent houses.",
                "current_hint_level": 0,
                "user_attempt": "I am unsure about the DP base case.",
            },
        )

    body = response.json()
    assert response.status_code == 200
    assert body["memory_context"]["applied"] is True
    assert body["memory_context"]["retrieved_count"] >= 1
    assert body["memory_context"]["provenance"][0]["source"] == "vector_memory.search"
    assert "prior memory" in body["mentor_note"]

    async with AsyncSessionLocal() as session:
        events = await learning_events_for_user(session, user_id, event_type="MemoryRetrieved", limit=5)

    assert events
    assert events[0].evidence["purpose"] == "hint_personalization"
    assert events[0].evidence["mastery_evidence"] is False
