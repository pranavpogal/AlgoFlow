# Gemini Advisory Expansion Report

## Purpose

Expand Gemini beyond problem classification and hints without replacing the
deterministic Skill/workflow system that anchors AlgoFlow's reliability.

## Before

- Gemini classification could adjudicate ambiguous problem analysis.
- Gemini hinting could improve selected hint responses.
- Code review, study planning, recommendations, pattern transfer, mock
  interviews, and analytics were deterministic only.
- Trace and policy records were deterministic evidence.

## After

AlgoFlow now supports optional Gemini advisory overlays for:

- Code review
- Study planning
- Recommendations
- Pattern transfer
- Mock interviews
- Analytics

Each feature has an independent flag:

- `ENABLE_GEMINI_CODE_REVIEW`
- `ENABLE_GEMINI_STUDY_PLAN`
- `ENABLE_GEMINI_RECOMMENDATIONS`
- `ENABLE_GEMINI_PATTERN_TRANSFER`
- `ENABLE_GEMINI_MOCK_INTERVIEW`
- `ENABLE_GEMINI_ANALYTICS`

Shared timeout:

- `GEMINI_ADVISORY_TIMEOUT_SECONDS`

## Architecture

The new `gemini_advisory` service returns structured advisory metadata:

```json
{
  "source": "gemini",
  "used": true,
  "task": "code_review_advisory",
  "model": "gemini-2.5-flash",
  "fallback_reason": null,
  "latency_ms": 123.4,
  "summary": "...",
  "suggestions": [],
  "cautions": [],
  "confidence": 0.72
}
```

When Gemini is disabled, missing, blocked, or times out, responses still return
deterministic output with a safe fallback reason.

## Safety Boundaries

- Gemini does not execute submitted code.
- Gemini cannot claim accepted verdicts or hidden test results.
- Gemini output is supplementary guidance, not mastery evidence.
- Gemini is not used to rewrite trace or policy records.
- Existing deterministic eval and CI baselines remain authoritative.

## Trace Decision

Trace, trajectory, and policy-decision records remain deterministic because they
are audit evidence. A model-generated trace would make debugging and evaluation
less trustworthy.

## Verification

- Focused Gemini advisory tests pass.
- Backend test suite passes.
- Backend lint passes.
- Accepted deterministic baseline comparison passes with no regressions.
- Frontend production build passes.
