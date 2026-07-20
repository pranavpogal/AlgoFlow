from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import BaseModel, Field, field_validator

from app.core.config import Settings, get_settings
from app.schemas.mentor import ProblemInput
from app.skills.problem_intelligence.workflow import ProblemClassificationResult


class GeminiClassificationEvidence(BaseModel):
    observed_evidence: str
    inferred_label: str
    confidence: float = Field(ge=0.0, le=1.0)
    cue_type: str


class GeminiClassificationResult(BaseModel):
    difficulty: str
    primary_topic: str
    primary_pattern: str
    sub_patterns: list[str] = Field(min_length=1, max_length=8)
    prerequisites: list[str] = Field(default_factory=list, max_length=8)
    reasoning: str = Field(min_length=20)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[GeminiClassificationEvidence] = Field(default_factory=list, max_length=8)
    risk_notes: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("difficulty")
    @classmethod
    def _difficulty_is_known_label(cls, value: str) -> str:
        allowed = {"Easy", "Medium", "Hard", "Unknown"}
        if value not in allowed:
            raise ValueError(f"difficulty must be one of {sorted(allowed)}")
        return value


@dataclass(frozen=True)
class ClassificationRiskDecision:
    should_call_gemini: bool
    reasons: list[str] = field(default_factory=list)
    risk_score: float = 0.0


@dataclass(frozen=True)
class ClassificationAdjudication:
    source: str
    deterministic: dict[str, Any]
    risk: ClassificationRiskDecision
    gemini: dict[str, Any] | None = None
    fallback_reason: str | None = None


class GeminiClassificationInvoker(Protocol):
    async def classify(
        self,
        *,
        payload: ProblemInput,
        deterministic: ProblemClassificationResult,
        risk: ClassificationRiskDecision,
    ) -> GeminiClassificationResult:
        ...


class GoogleGenerativeAIClassificationInvoker:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def classify(
        self,
        *,
        payload: ProblemInput,
        deterministic: ProblemClassificationResult,
        risk: ClassificationRiskDecision,
    ) -> GeminiClassificationResult:
        if not self.settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is required for Gemini classification.")

        async with asyncio.timeout(self.settings.gemini_classification_timeout_seconds):
            return await asyncio.to_thread(self._classify_sync, payload, deterministic, risk)

    def _classify_sync(
        self,
        payload: ProblemInput,
        deterministic: ProblemClassificationResult,
        risk: ClassificationRiskDecision,
    ) -> GeminiClassificationResult:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.settings.google_api_key)
        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=_prompt(payload, deterministic, risk),
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
        raw_text = getattr(response, "text", "") or ""
        return parse_gemini_classification(raw_text)


def detect_classification_risk(
    payload: ProblemInput,
    deterministic: ProblemClassificationResult,
) -> ClassificationRiskDecision:
    reasons: list[str] = []
    risk_score = 0.0
    provenance = {item.value for item in deterministic.provenance}
    haystack = f"{payload.title} {payload.description}".lower()

    if "CURATED_METADATA" in provenance:
        return ClassificationRiskDecision(False, ["curated_metadata_trusted"], 0.0)

    if deterministic.confidence <= 0.82:
        reasons.append("low_or_moderate_deterministic_confidence")
        risk_score += 0.35

    if deterministic.secondary_topics:
        reasons.append("competing_secondary_topics")
        risk_score += 0.25

    if deterministic.primary_topic == "General Problem Solving":
        reasons.append("generic_fallback_classification")
        risk_score += 0.5

    ambiguity_terms = {
        "maximum",
        "minimum",
        "longest",
        "fewest",
        "optimal",
        "choose",
        "select",
        "partition",
        "schedule",
        "interval",
        "subsequence",
        "profit",
        "reach",
        "cost",
    }
    matched_terms = sorted(term for term in ambiguity_terms if term in haystack)
    if len(matched_terms) >= 2:
        reasons.append(f"optimization_ambiguity_terms:{','.join(matched_terms[:5])}")
        risk_score += 0.25

    confusion_families = [
        ("greedy_dp_conflict", ["greedy", "dp", "dynamic programming", "minimum", "maximum", "longest"]),
        ("interval_greedy_weighted_dp_conflict", ["interval", "profit", "weighted", "non-overlapping", "schedule"]),
        ("lis_greedy_conflict", ["subsequence", "chain", "increasing", "wiggle"]),
        ("sliding_window_prefix_sum_conflict", ["subarray", "sum", "at least", "equals k"]),
        ("binary_search_answer_dp_conflict", ["minimize maximum", "minimum capacity", "split", "feasible"]),
        ("graph_search_backtracking_conflict", ["remove", "minimum", "valid", "state", "bfs", "backtracking"]),
    ]
    for label, terms in confusion_families:
        hits = [term for term in terms if term in haystack]
        if len(hits) >= 2:
            reasons.append(label)
            risk_score += 0.3

    from_broad_rules = "No model inference was used" in " ".join(deterministic.unsupported_claims)
    if from_broad_rules and risk_score >= 0.3:
        reasons.append("broad_rule_high_false_confidence_risk")
        risk_score += 0.2

    risk_score = round(min(1.0, risk_score), 2)
    return ClassificationRiskDecision(risk_score >= 0.5, reasons or ["low_risk"], risk_score)


async def adjudicate_classification(
    *,
    payload: ProblemInput,
    deterministic: ProblemClassificationResult,
    settings: Settings | None = None,
    invoker: GeminiClassificationInvoker | None = None,
) -> ClassificationAdjudication:
    settings = settings or get_settings()
    risk = detect_classification_risk(payload, deterministic)
    deterministic_payload = deterministic.to_legacy_dict()
    if not risk.should_call_gemini:
        return ClassificationAdjudication("deterministic", deterministic_payload, risk)
    if not settings.enable_gemini_classification:
        return ClassificationAdjudication(
            "deterministic",
            deterministic_payload,
            risk,
            fallback_reason="gemini_classification_disabled",
        )
    if not settings.google_api_key and invoker is None:
        return ClassificationAdjudication(
            "deterministic",
            deterministic_payload,
            risk,
            fallback_reason="missing_google_api_key",
        )

    try:
        selected_invoker = invoker or GoogleGenerativeAIClassificationInvoker(settings)
        gemini_result = await selected_invoker.classify(
            payload=payload,
            deterministic=deterministic,
            risk=risk,
        )
    except Exception as exc:
        return ClassificationAdjudication(
            "deterministic",
            deterministic_payload,
            risk,
            fallback_reason=f"gemini_classification_failed:{_exception_label(exc)}",
        )

    return ClassificationAdjudication(
        "gemini",
        deterministic_payload,
        risk,
        gemini=_gemini_to_legacy_payload(payload, gemini_result),
    )


def parse_gemini_classification(raw_text: str) -> GeminiClassificationResult:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return GeminiClassificationResult.model_validate_json(text)


def _exception_label(exc: Exception) -> str:
    status = getattr(exc, "status_code", None)
    message = _sanitize_exception_message(str(exc))
    parts = [type(exc).__name__]
    if status:
        parts.append(str(status))
    if message:
        parts.append(message)
    return ":".join(parts)


def _sanitize_exception_message(message: str) -> str:
    collapsed = " ".join(message.split())
    redacted = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[redacted-api-key]", collapsed)
    return redacted[:240]


def _gemini_to_legacy_payload(payload: ProblemInput, result: GeminiClassificationResult) -> dict[str, Any]:
    return {
        "difficulty": result.difficulty,
        "pattern": result.primary_topic,
        "sub_patterns": result.sub_patterns,
        "prerequisites": result.prerequisites,
        "reasoning": result.reasoning,
        "primary_topic": result.primary_topic,
        "secondary_topics": [],
        "primary_pattern": result.primary_pattern,
        "structural_cues": [item.cue_type for item in result.evidence],
        "related_patterns": [],
        "difficulty_signals": ["gemini_semantic_adjudication"],
        "confidence": result.confidence,
        "evidence": [
            {
                "observed_evidence": item.observed_evidence,
                "inferred_label": item.inferred_label,
                "confidence": item.confidence,
                "provenance": "MODEL_INFERENCE",
                "cue_type": item.cue_type,
            }
            for item in result.evidence
        ],
        "provenance": ["MODEL_INFERENCE"],
        "unsupported_claims": [
            "Gemini classification is semantic pattern evidence, not learner mastery evidence.",
            *result.risk_notes,
        ],
        "taxonomy_version": "problem-intelligence-taxonomy-v1+gemini-adjudication-v1",
        "problem": payload.title,
    }


def _prompt(
    payload: ProblemInput,
    deterministic: ProblemClassificationResult,
    risk: ClassificationRiskDecision,
) -> str:
    return json.dumps(
        {
            "role": "You are AlgoFlow's coding-interview pattern classifier.",
            "task": (
                "Classify the problem semantically. Pay special attention to Greedy vs DP, "
                "LIS vs Greedy, interval greedy vs weighted interval DP, binary-search-on-answer vs DP, "
                "sliding window vs prefix sum, and graph search vs backtracking. Return only valid JSON."
            ),
            "required_schema": {
                "difficulty": "Easy|Medium|Hard|Unknown",
                "primary_topic": "string",
                "primary_pattern": "string",
                "sub_patterns": ["string"],
                "prerequisites": ["string"],
                "reasoning": "string",
                "confidence": "number between 0 and 1",
                "evidence": [
                    {
                        "observed_evidence": "short quote or paraphrase from statement",
                        "inferred_label": "topic or pattern inferred",
                        "confidence": "number between 0 and 1",
                        "cue_type": "semantic cue category",
                    }
                ],
                "risk_notes": ["string"],
            },
            "problem": {
                "number": payload.problem_number,
                "title": payload.title,
                "url": payload.url,
                "description": payload.description,
            },
            "deterministic_result": deterministic.to_legacy_dict(),
            "risk_detector": {
                "risk_score": risk.risk_score,
                "reasons": risk.reasons,
            },
        },
        indent=2,
    )
