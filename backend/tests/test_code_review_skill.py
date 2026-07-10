import pytest
from httpx import ASGITransport, AsyncClient

from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal
from app.main import app
from app.memory.repository import learning_events_for_user
from app.skills.code_review.workflow import CodeReviewContext, ReviewIntent, review_code_workflow


@pytest.fixture(autouse=True)
async def sync_test_schema():
    await init_db()


def test_python_review_produces_structured_boundary_finding():
    code = "def rob(nums):\n    dp = [0] * len(nums)\n    for i in range(len(nums)):\n        dp[i] = max(dp[i-1], nums[i] + dp[i-2])\n    return dp[-1]"
    result = review_code_workflow(
        CodeReviewContext(title="House Robber", language="Python", code=code, user_intent="find the bug")
    )

    assert result.intent == ReviewIntent.FIND_BUG
    assert result.language_supported is True
    assert "python_ast_parse" in result.analysis_layers
    categories = {finding.category.value for finding in result.findings}
    assert "boundary" in categories
    assert all(finding.provenance for finding in result.findings)
    assert any(finding.location.line_start is not None for finding in result.findings)
    assert result.corrected_code is None


def test_do_not_rewrite_intent_preserves_learner_ownership():
    code = "def rob(nums):\n    dp = [0] * len(nums)\n    for i in range(len(nums)):\n        dp[i] = dp[i-1]\n    return dp[-1]"
    result = review_code_workflow(
        CodeReviewContext(
            title="House Robber",
            language="Python",
            code=code,
            user_intent="Find the bug but don't rewrite my code",
        )
    )

    assert result.intent == ReviewIntent.DO_NOT_REWRITE
    assert result.corrected_code is None
    assert result.rewrite_allowed is False
    assert "not rewrite" in result.senior_engineer_summary.lower()


def test_corrected_code_requires_explicit_intent():
    code = "def rob(nums):\n    dp = [0] * len(nums)\n    for i in range(len(nums)):\n        dp[i] = max(dp[i-1], nums[i] + dp[i-2])\n    return dp[-1]"
    result = review_code_workflow(
        CodeReviewContext(
            title="House Robber",
            language="Python",
            code=code,
            user_intent="Give corrected code and explain the root cause",
        )
    )

    assert result.intent == ReviewIntent.PROVIDE_CORRECTED_CODE
    assert result.rewrite_allowed is True
    assert result.corrected_code is not None
    assert "def rob" in result.corrected_code


def test_unsupported_language_degrades_honestly():
    result = review_code_workflow(
        CodeReviewContext(title="Two Sum", language="Rust", code="fn main() {}", user_intent="review my code")
    )

    assert result.language_supported is False
    assert "unsupported_language_notice" in result.analysis_layers
    assert any("No AST-backed" in claim for claim in result.unsupported_claims)
    assert {finding.category.value for finding in result.findings} == {"unsupported_language"}


@pytest.mark.asyncio
async def test_code_review_api_records_evidence_aware_events():
    user_id = "phase-4b-review-user"
    code = "def rob(nums):\n    dp = [0] * len(nums)\n    for i in range(len(nums)):\n        dp[i] = max(dp[i-1], nums[i] + dp[i-2])\n    return dp[-1]"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/code-review",
            headers={"x-user-id": user_id},
            json={
                "title": "House Robber",
                "language": "Python",
                "code": code,
                "user_intent": "Find the bug but don't rewrite my code",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["review_intent"] == "DO_NOT_REWRITE"
    assert payload["findings"]
    assert payload["corrected_code"] is None
    assert payload["language_supported"] is True

    async with AsyncSessionLocal() as session:
        events = await learning_events_for_user(session, user_id, limit=20)

    event_types = {event.event_type for event in events}
    assert "CodeReviewRequested" in event_types
    assert "CodeReviewCompleted" in event_types
    assert "CodeFindingProduced" in event_types
    completed = next(event for event in events if event.event_type == "CodeReviewCompleted")
    assert completed.evidence["finding_count"] >= 1
    assert completed.evidence["rewrite_allowed"] is False
