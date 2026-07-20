from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Protocol

from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings, get_settings
from app.schemas.mentor import HintRequest
from app.skills.progressive_hinting.workflow import HintContext, ProgressiveHintResult


class GeminiHintResult(BaseModel):
    hint: str = Field(min_length=20, max_length=900)
    mentor_note: str = Field(min_length=10, max_length=500)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_focus: str = Field(min_length=3, max_length=120)
    risk_notes: list[str] = Field(default_factory=list, max_length=6)


@dataclass(frozen=True)
class HintRiskDecision:
    should_call_gemini: bool
    reasons: list[str] = field(default_factory=list)
    risk_score: float = 0.0


@dataclass(frozen=True)
class HintAdjudication:
    source: str
    deterministic_hint: str
    deterministic_mentor_note: str
    risk: HintRiskDecision
    gemini_hint: str | None = None
    gemini_mentor_note: str | None = None
    fallback_reason: str | None = None


class GeminiHintInvoker(Protocol):
    async def generate(
        self,
        *,
        payload: HintRequest,
        context: HintContext,
        deterministic: ProgressiveHintResult,
        risk: HintRiskDecision,
    ) -> GeminiHintResult:
        ...


class GoogleGenerativeAIHintInvoker:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def generate(
        self,
        *,
        payload: HintRequest,
        context: HintContext,
        deterministic: ProgressiveHintResult,
        risk: HintRiskDecision,
    ) -> GeminiHintResult:
        if not self.settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is required for Gemini hints.")
        async with asyncio.timeout(self.settings.gemini_hint_timeout_seconds):
            return await asyncio.to_thread(self._generate_sync, payload, context, deterministic, risk)

    def _generate_sync(
        self,
        payload: HintRequest,
        context: HintContext,
        deterministic: ProgressiveHintResult,
        risk: HintRiskDecision,
    ) -> GeminiHintResult:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.settings.google_api_key)
        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=_prompt(payload, context, deterministic, risk),
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        raw_text = getattr(response, "text", "") or ""
        return parse_gemini_hint(raw_text)


def detect_hint_risk(context: HintContext, deterministic: ProgressiveHintResult) -> HintRiskDecision:
    reasons: list[str] = []
    risk_score = 0.0
    text = f"{context.title} {context.description} {context.user_attempt or ''}".lower()

    if context.reveal_solution:
        return HintRiskDecision(False, ["explicit_solution_path_uses_deterministic_guardrail"], 0.0)

    complex_patterns = [
        "weighted interval",
        "lis",
        "dynamic programming and binary search",
        "greedy",
        "backtracking",
        "graph search",
        "binary search on answer",
        "prefix sum",
    ]
    if any(pattern in context.pattern.lower() for pattern in complex_patterns):
        reasons.append("complex_pattern_hinting")
        risk_score += 0.3

    ambiguity_terms = ["maximum", "minimum", "longest", "fewest", "optimal", "choose", "state", "greedy", "dp"]
    hits = [term for term in ambiguity_terms if term in text]
    if len(hits) >= 2:
        reasons.append(f"ambiguous_hint_context:{','.join(hits[:5])}")
        risk_score += 0.3

    if context.user_attempt:
        reasons.append("user_attempt_needs_interpretation")
        risk_score += 0.25

    if deterministic.uses_previous_hint_context:
        reasons.append("multi_turn_hint_context")
        risk_score += 0.2

    if deterministic.hint.startswith("What is the smallest subproblem"):
        reasons.append("generic_deterministic_hint")
        risk_score += 0.35

    risk_score = round(min(1.0, risk_score), 2)
    return HintRiskDecision(risk_score >= 0.5, reasons or ["low_risk"], risk_score)


async def adjudicate_hint(
    *,
    payload: HintRequest,
    context: HintContext,
    deterministic: ProgressiveHintResult,
    settings: Settings | None = None,
    invoker: GeminiHintInvoker | None = None,
) -> HintAdjudication:
    settings = settings or get_settings()
    risk = detect_hint_risk(context, deterministic)
    if not risk.should_call_gemini:
        return HintAdjudication("deterministic", deterministic.hint, deterministic.mentor_note, risk)
    if not settings.enable_gemini_hints:
        return HintAdjudication(
            "deterministic",
            deterministic.hint,
            deterministic.mentor_note,
            risk,
            fallback_reason="gemini_hints_disabled",
        )
    if not settings.google_api_key and invoker is None:
        return HintAdjudication(
            "deterministic",
            deterministic.hint,
            deterministic.mentor_note,
            risk,
            fallback_reason="missing_google_api_key",
        )

    try:
        selected_invoker = invoker or GoogleGenerativeAIHintInvoker(settings)
        gemini = await selected_invoker.generate(
            payload=payload,
            context=context,
            deterministic=deterministic,
            risk=risk,
        )
    except (asyncio.TimeoutError, ValidationError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        return HintAdjudication(
            "deterministic",
            deterministic.hint,
            deterministic.mentor_note,
            risk,
            fallback_reason=f"gemini_hint_failed:{type(exc).__name__}",
        )

    if _leaks_solution(gemini.hint, reveal_allowed=context.reveal_solution):
        return HintAdjudication(
            "deterministic",
            deterministic.hint,
            deterministic.mentor_note,
            risk,
            fallback_reason="gemini_hint_rejected_solution_leakage",
        )

    return HintAdjudication(
        "gemini",
        deterministic.hint,
        deterministic.mentor_note,
        risk,
        gemini_hint=gemini.hint,
        gemini_mentor_note=gemini.mentor_note,
    )


def parse_gemini_hint(raw_text: str) -> GeminiHintResult:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return GeminiHintResult.model_validate_json(text)


def _leaks_solution(text: str, *, reveal_allowed: bool) -> bool:
    if reveal_allowed:
        return False
    lowered = text.lower()
    leak_markers = [
        "full solution",
        "here is the solution",
        "the recurrence is",
        "dp[i] =",
        "return ",
        "for i in range",
        "class solution",
        "def ",
        "public ",
        "#include",
    ]
    return any(marker in lowered for marker in leak_markers)


def _prompt(
    payload: HintRequest,
    context: HintContext,
    deterministic: ProgressiveHintResult,
    risk: HintRiskDecision,
) -> str:
    return json.dumps(
        {
            "role": "You are AlgoFlow's progressive coding-interview hint mentor.",
            "task": (
                "Generate one contextual hint. Do not solve the problem, do not provide code, "
                "and do not reveal recurrence formulas unless reveal_solution is true. The hint "
                "should help the learner discover the next idea themselves."
            ),
            "required_schema": {
                "hint": "one hint, no full solution",
                "mentor_note": "why this hint is appropriate",
                "confidence": "number between 0 and 1",
                "reasoning_focus": "short focus label",
                "risk_notes": ["string"],
            },
            "problem": {
                "number": payload.problem_number,
                "title": payload.title,
                "description": payload.description,
                "pattern": context.pattern,
                "difficulty": context.difficulty,
            },
            "learner": {
                "current_hint_level": context.current_hint_level,
                "user_attempt": context.user_attempt,
                "reveal_solution": context.reveal_solution,
                "learner_state": context.learner_state,
            },
            "deterministic_hint": {
                "hint": deterministic.hint,
                "mentor_note": deterministic.mentor_note,
                "intervention_type": deterministic.intervention_type.value,
                "intent": deterministic.intent.value,
                "reveals_solution": deterministic.reveals_solution,
            },
            "risk_detector": {
                "risk_score": risk.risk_score,
                "reasons": risk.reasons,
            },
        },
        indent=2,
    )
