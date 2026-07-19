import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.db.init_db import init_db
from app.main import app
from app.schemas.mentor import HintRequest
from app.services import mentor_service as mentor_module
from app.skills.progressive_hinting.gemini_adjudicator import (
    GeminiHintResult,
    HintAdjudication,
    HintRiskDecision,
    adjudicate_hint,
    detect_hint_risk,
)
from app.skills.progressive_hinting.workflow import HintContext, generate_progressive_hint


@pytest.fixture(autouse=True)
async def sync_test_schema():
    await init_db()


class FakeHintInvoker:
    def __init__(self, hint: str) -> None:
        self.hint = hint

    async def generate(self, *, payload, context, deterministic, risk):
        return GeminiHintResult(
            hint=self.hint,
            mentor_note="This keeps the learner focused on the next idea without revealing the full method.",
            confidence=0.88,
            reasoning_focus="semantic next-step hint",
        )


def _risky_hint_inputs() -> tuple[HintRequest, HintContext]:
    payload = HintRequest(
        title="Conference Profit Planner",
        description=(
            "Given jobs with start times, end times, and profits, select non-overlapping jobs "
            "to maximize total profit."
        ),
        current_hint_level=1,
        user_attempt="I am choosing earliest ending jobs greedily, but the profit part is confusing.",
    )
    context = HintContext(
        title=payload.title,
        description=payload.description,
        pattern="Dynamic Programming and Binary Search",
        difficulty="Hard",
        current_hint_level=payload.current_hint_level,
        user_attempt=payload.user_attempt,
        reveal_solution=False,
        learner_state={"confidence": "unknown", "weak_topics": []},
        previous_hint_events=[],
    )
    return payload, context


def test_hint_risk_detector_flags_complex_user_attempt():
    payload, context = _risky_hint_inputs()
    deterministic = generate_progressive_hint(context)

    risk = detect_hint_risk(context, deterministic)

    assert risk.should_call_gemini is True
    assert "user_attempt_needs_interpretation" in risk.reasons


@pytest.mark.asyncio
async def test_gemini_hint_is_used_when_enabled_and_safe():
    payload, context = _risky_hint_inputs()
    deterministic = generate_progressive_hint(context)

    adjudication = await adjudicate_hint(
        payload=payload,
        context=context,
        deterministic=deterministic,
        settings=Settings(enable_gemini_hints=True, google_api_key="test-key"),
        invoker=FakeHintInvoker(
            "The profit value changes the decision: ask yourself what information you would need "
            "about the best compatible job before deciding whether to take the current one."
        ),
    )

    assert adjudication.source == "gemini"
    assert adjudication.gemini_hint is not None
    assert "best compatible job" in adjudication.gemini_hint


@pytest.mark.asyncio
async def test_gemini_hint_falls_back_when_disabled():
    payload, context = _risky_hint_inputs()
    deterministic = generate_progressive_hint(context)

    adjudication = await adjudicate_hint(
        payload=payload,
        context=context,
        deterministic=deterministic,
        settings=Settings(enable_gemini_hints=False, google_api_key="test-key"),
        invoker=FakeHintInvoker("This safe fake hint should not be used when the feature is disabled."),
    )

    assert adjudication.source == "deterministic"
    assert adjudication.fallback_reason == "gemini_hints_disabled"


@pytest.mark.asyncio
async def test_gemini_hint_rejects_solution_leakage():
    payload, context = _risky_hint_inputs()
    deterministic = generate_progressive_hint(context)

    adjudication = await adjudicate_hint(
        payload=payload,
        context=context,
        deterministic=deterministic,
        settings=Settings(enable_gemini_hints=True, google_api_key="test-key"),
        invoker=FakeHintInvoker("The recurrence is dp[i] = max(dp[i - 1], profit[i] + dp[p[i]])."),
    )

    assert adjudication.source == "deterministic"
    assert adjudication.fallback_reason == "gemini_hint_rejected_solution_leakage"


@pytest.mark.asyncio
async def test_hint_api_can_return_gemini_hint(monkeypatch):
    async def fake_adjudicate_hint(*, payload, context, deterministic):
        return HintAdjudication(
            source="gemini",
            deterministic_hint=deterministic.hint,
            deterministic_mentor_note=deterministic.mentor_note,
            risk=HintRiskDecision(True, ["complex_pattern_hinting"], 0.75),
            gemini_hint="Focus on why profit breaks the earliest-ending greedy choice before choosing a state.",
            gemini_mentor_note="Gemini refined this hint for the ambiguity in the user attempt.",
        )

    monkeypatch.setattr(mentor_module, "adjudicate_hint", fake_adjudicate_hint)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/hints/next",
            headers={"x-user-id": "gemini-hint-user"},
            json={
                "title": "Conference Profit Planner",
                "description": (
                    "Given jobs with start times, end times, and profits, select non-overlapping jobs "
                    "to maximize total profit."
                ),
                "current_hint_level": 1,
                "user_attempt": "I am trying earliest finish time greedily.",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["hint_source"] == "gemini"
    assert body["hint_adjudication"]["gemini_used"] is True
