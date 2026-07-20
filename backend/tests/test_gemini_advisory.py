import pytest

from app.core.config import Settings
from app.services.gemini_advisory import (
    GeminiAdvisoryResult,
    maybe_generate_gemini_advisory,
    parse_gemini_advisory,
)


class FakeAdvisoryInvoker:
    async def generate(self, *, task, context, deterministic_response):
        return GeminiAdvisoryResult(
            summary=f"Advisory for {task}",
            suggestions=["Ask for the invariant before discussing code."],
            cautions=["Treat this as supplementary guidance."],
            confidence=0.72,
        )


class FailingAdvisoryInvoker:
    async def generate(self, *, task, context, deterministic_response):
        raise RuntimeError("bad key AIza123456789012345678901234567890")


@pytest.mark.asyncio
async def test_gemini_advisory_disabled_uses_deterministic_fallback():
    advisory = await maybe_generate_gemini_advisory(
        task="code_review_advisory",
        enabled=False,
        context={},
        deterministic_response={},
        settings=Settings(google_api_key="test-key"),
        invoker=FakeAdvisoryInvoker(),
    )

    assert advisory["used"] is False
    assert advisory["source"] == "deterministic"
    assert advisory["fallback_reason"] == "gemini_advisory_disabled"


@pytest.mark.asyncio
async def test_gemini_advisory_missing_credentials_falls_back_without_invoker():
    advisory = await maybe_generate_gemini_advisory(
        task="study_plan_advisory",
        enabled=True,
        context={},
        deterministic_response={},
        settings=Settings(google_api_key=None),
    )

    assert advisory["used"] is False
    assert advisory["fallback_reason"] == "missing_gemini_credentials"


@pytest.mark.asyncio
async def test_gemini_advisory_success_returns_structured_metadata():
    advisory = await maybe_generate_gemini_advisory(
        task="mock_interview_advisory",
        enabled=True,
        context={"stage": "approach"},
        deterministic_response={"interviewer_message": "Explain your approach."},
        settings=Settings(google_api_key=None),
        invoker=FakeAdvisoryInvoker(),
    )

    assert advisory["used"] is True
    assert advisory["source"] == "gemini"
    assert advisory["summary"] == "Advisory for mock_interview_advisory"
    assert advisory["confidence"] == 0.72


@pytest.mark.asyncio
async def test_gemini_advisory_failure_is_sanitized():
    advisory = await maybe_generate_gemini_advisory(
        task="analytics_advisory",
        enabled=True,
        context={},
        deterministic_response={},
        settings=Settings(google_api_key=None),
        invoker=FailingAdvisoryInvoker(),
    )

    assert advisory["used"] is False
    assert "RuntimeError" in advisory["fallback_reason"]
    assert "[redacted-api-key]" in advisory["fallback_reason"]
    assert "AIza" not in advisory["fallback_reason"]


def test_parse_gemini_advisory_accepts_json_fence():
    parsed = parse_gemini_advisory(
        """
        ```json
        {
          "summary": "Focus on explaining the invariant first.",
          "suggestions": ["Name the state before recurrence."],
          "cautions": ["Do not claim execution."],
          "confidence": 0.8
        }
        ```
        """
    )

    assert parsed.summary == "Focus on explaining the invariant first."
    assert parsed.confidence == 0.8
