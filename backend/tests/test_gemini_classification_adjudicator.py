import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.db.init_db import init_db
from app.main import app
from app.schemas.mentor import ProblemInput
from app.services import mentor_service as mentor_module
from app.skills.problem_intelligence.gemini_adjudicator import (
    ClassificationAdjudication,
    ClassificationRiskDecision,
    GeminiClassificationEvidence,
    GeminiClassificationResult,
    adjudicate_classification,
    detect_classification_risk,
)
from app.skills.problem_intelligence.workflow import ProblemClassificationContext, classify_problem


@pytest.fixture(autouse=True)
async def sync_test_schema():
    await init_db()


class FakeGeminiInvoker:
    async def classify(self, *, payload, deterministic, risk):
        return GeminiClassificationResult(
            difficulty="Hard",
            primary_topic="Dynamic Programming and Binary Search",
            primary_pattern="Weighted Interval Scheduling",
            sub_patterns=["Sort by Time", "Binary Search Previous Compatible Job", "Take-or-Skip DP"],
            prerequisites=["Dynamic Programming", "Binary Search", "Intervals"],
            reasoning=(
                "The profit weight makes earliest-finish greedy unsafe, so the solution needs a "
                "take-or-skip recurrence over jobs plus binary search for the previous compatible job."
            ),
            confidence=0.9,
            evidence=[
                GeminiClassificationEvidence(
                    observed_evidence="select non-overlapping jobs to maximize total profit",
                    inferred_label="Weighted Interval Scheduling",
                    confidence=0.9,
                    cue_type="weighted interval optimization",
                )
            ],
        )


def test_risk_detector_flags_weighted_interval_confusion():
    payload = ProblemInput(
        title="Conference Profit Planner",
        description=(
            "Given jobs with start times, end times, and profits, select non-overlapping jobs "
            "to maximize total profit."
        ),
    )
    deterministic = classify_problem(
        ProblemClassificationContext(title=payload.title, description=payload.description)
    )

    risk = detect_classification_risk(payload, deterministic)

    assert risk.should_call_gemini is True
    assert "interval_greedy_weighted_dp_conflict" in risk.reasons
    assert risk.risk_score >= 0.5


@pytest.mark.asyncio
async def test_adjudicator_uses_gemini_for_risky_classification_with_valid_schema():
    payload = ProblemInput(
        title="Conference Profit Planner",
        description=(
            "Given jobs with start times, end times, and profits, select non-overlapping jobs "
            "to maximize total profit."
        ),
    )
    deterministic = classify_problem(
        ProblemClassificationContext(title=payload.title, description=payload.description)
    )

    adjudication = await adjudicate_classification(
        payload=payload,
        deterministic=deterministic,
        settings=Settings(enable_gemini_classification=True, google_api_key="test-key"),
        invoker=FakeGeminiInvoker(),
    )

    assert adjudication.source == "gemini"
    assert adjudication.gemini is not None
    assert adjudication.gemini["primary_pattern"] == "Weighted Interval Scheduling"
    assert adjudication.gemini["provenance"] == ["MODEL_INFERENCE"]


@pytest.mark.asyncio
async def test_adjudicator_falls_back_when_gemini_is_disabled():
    payload = ProblemInput(
        title="Conference Profit Planner",
        description=(
            "Given jobs with start times, end times, and profits, select non-overlapping jobs "
            "to maximize total profit."
        ),
    )
    deterministic = classify_problem(
        ProblemClassificationContext(title=payload.title, description=payload.description)
    )

    adjudication = await adjudicate_classification(
        payload=payload,
        deterministic=deterministic,
        settings=Settings(enable_gemini_classification=False, google_api_key="test-key"),
        invoker=FakeGeminiInvoker(),
    )

    assert adjudication.source == "deterministic"
    assert adjudication.fallback_reason == "gemini_classification_disabled"


@pytest.mark.asyncio
async def test_analyze_problem_can_return_gemini_adjudicated_classification(monkeypatch):
    async def fake_adjudicate_classification(*, payload, deterministic):
        gemini = {
            "difficulty": "Hard",
            "pattern": "Dynamic Programming and Binary Search",
            "sub_patterns": ["Sort by Time", "Binary Search Previous Compatible Job", "Take-or-Skip DP"],
            "prerequisites": ["Dynamic Programming", "Binary Search", "Intervals"],
            "reasoning": "Gemini adjudicated this as weighted interval scheduling.",
            "primary_topic": "Dynamic Programming and Binary Search",
            "secondary_topics": [],
            "primary_pattern": "Weighted Interval Scheduling",
            "structural_cues": ["weighted interval optimization"],
            "related_patterns": [],
            "difficulty_signals": ["gemini_semantic_adjudication"],
            "confidence": 0.9,
            "evidence": [],
            "provenance": ["MODEL_INFERENCE"],
            "unsupported_claims": ["Gemini classification is semantic pattern evidence."],
            "taxonomy_version": "test-gemini-adjudication",
        }
        return ClassificationAdjudication(
            source="gemini",
            deterministic=deterministic.to_legacy_dict(),
            risk=ClassificationRiskDecision(True, ["interval_greedy_weighted_dp_conflict"], 0.8),
            gemini=gemini,
        )

    monkeypatch.setattr(mentor_module, "adjudicate_classification", fake_adjudicate_classification)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/problems/analyze",
            headers={"x-user-id": "gemini-adjudication-user"},
            json={
                "title": "Conference Profit Planner",
                "description": (
                    "Given jobs with start times, end times, and profits, select non-overlapping jobs "
                    "to maximize total profit."
                ),
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["classification_source"] == "gemini"
    assert body["primary_pattern"] == "Weighted Interval Scheduling"
    assert body["classification_adjudication"]["risk"]["should_call_gemini"] is True
