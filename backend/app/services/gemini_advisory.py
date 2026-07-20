from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.skills.problem_intelligence.gemini_adjudicator import _sanitize_exception_message


class GeminiAdvisoryResult(BaseModel):
    summary: str = Field(min_length=10, max_length=700)
    suggestions: list[str] = Field(default_factory=list, max_length=6)
    cautions: list[str] = Field(default_factory=list, max_length=6)
    confidence: float = Field(ge=0.0, le=1.0)


class GeminiAdvisoryInvoker(Protocol):
    async def generate(
        self,
        *,
        task: str,
        context: dict[str, Any],
        deterministic_response: dict[str, Any],
    ) -> GeminiAdvisoryResult:
        ...


class GoogleGenAIAdvisoryInvoker:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def generate(
        self,
        *,
        task: str,
        context: dict[str, Any],
        deterministic_response: dict[str, Any],
    ) -> GeminiAdvisoryResult:
        if not self.settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is required for Gemini advisory generation.")
        async with asyncio.timeout(self.settings.gemini_advisory_timeout_seconds):
            return await asyncio.to_thread(
                self._generate_sync,
                task,
                context,
                deterministic_response,
            )

    def _generate_sync(
        self,
        task: str,
        context: dict[str, Any],
        deterministic_response: dict[str, Any],
    ) -> GeminiAdvisoryResult:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.settings.google_api_key)
        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=_prompt(task, context, deterministic_response),
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        return parse_gemini_advisory(getattr(response, "text", "") or "")


async def maybe_generate_gemini_advisory(
    *,
    task: str,
    enabled: bool,
    context: dict[str, Any],
    deterministic_response: dict[str, Any],
    settings: Settings | None = None,
    invoker: GeminiAdvisoryInvoker | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    started = time.perf_counter()
    base = {
        "source": "deterministic",
        "used": False,
        "task": task,
        "model": settings.gemini_model,
        "fallback_reason": None,
        "latency_ms": None,
        "summary": None,
        "suggestions": [],
        "cautions": [],
        "confidence": None,
    }
    if not enabled:
        return {**base, "fallback_reason": "gemini_advisory_disabled"}
    if not settings.google_api_key and invoker is None:
        return {**base, "fallback_reason": "missing_google_api_key"}

    try:
        selected_invoker = invoker or GoogleGenAIAdvisoryInvoker(settings)
        advisory = await selected_invoker.generate(
            task=task,
            context=context,
            deterministic_response=deterministic_response,
        )
    except Exception as exc:
        return {
            **base,
            "fallback_reason": f"gemini_advisory_failed:{_exception_label(exc)}",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    return {
        **base,
        "source": "gemini",
        "used": True,
        "fallback_reason": None,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "summary": advisory.summary,
        "suggestions": advisory.suggestions,
        "cautions": advisory.cautions,
        "confidence": advisory.confidence,
    }


def parse_gemini_advisory(raw_text: str) -> GeminiAdvisoryResult:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return GeminiAdvisoryResult.model_validate_json(text)


def _exception_label(exc: Exception) -> str:
    status = getattr(exc, "status_code", None)
    message = _sanitize_exception_message(str(exc))
    parts = [type(exc).__name__]
    if status:
        parts.append(str(status))
    if message:
        parts.append(message)
    return ":".join(parts)


def _prompt(task: str, context: dict[str, Any], deterministic_response: dict[str, Any]) -> str:
    return json.dumps(
        {
            "role": "You are AlgoFlow's optional Gemini advisory layer.",
            "task": task,
            "rules": [
                "Do not replace deterministic workflow output.",
                "Do not claim code execution, accepted verdicts, or hidden test results.",
                "Do not expose full solutions unless the deterministic response already permits it.",
                "Use retrieved memory only as advisory personalization, never as proof of mastery.",
                "Return only valid JSON matching the required schema.",
            ],
            "required_schema": {
                "summary": "short mentor-facing advisory summary",
                "suggestions": ["bounded suggestions that improve the deterministic response"],
                "cautions": ["limitations, uncertainty, or safety notes"],
                "confidence": "number between 0 and 1",
            },
            "trusted_context": context,
            "deterministic_response": deterministic_response,
        },
        indent=2,
        default=str,
    )
