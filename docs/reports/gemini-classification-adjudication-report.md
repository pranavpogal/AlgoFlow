# Gemini Classification Adjudication Report

## Scope

Add a narrow Gemini-assisted classification layer for Analyze Problem when deterministic pattern detection is risky or ambiguous.

This phase does not replace deterministic workflows, broaden ADK routing, add new tool autonomy, or mutate the accepted deterministic baseline. Gemini acts as a semantic adjudicator only after deterministic classification and risk detection.

## Runtime Flow

```text
Analyze Problem request
↓
Deterministic classifier runs first
↓
Risk detector evaluates false-confidence risk
↓
If low risk: return deterministic result
↓
If risky and ENABLE_GEMINI_CLASSIFICATION=true and GOOGLE_API_KEY exists: call Gemini
↓
Validate Gemini JSON with Pydantic
↓
Return Gemini classification if valid
↓
Otherwise fall back to deterministic result
```

## Gemini Routing Triggers

The risk detector can route to Gemini for:

- Low or moderate deterministic confidence
- Generic fallback classification
- Competing secondary topics
- Greedy-vs-DP ambiguity
- LIS-vs-Greedy ambiguity
- Weighted interval scheduling vs interval greedy
- Binary-search-on-answer vs DP
- Sliding window vs prefix sum
- Graph search vs backtracking
- Broad keyword-rule matches on optimization-heavy statements

Curated metadata remains trusted and does not call Gemini.

## Configuration

```bash
GOOGLE_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
ENABLE_GEMINI_CLASSIFICATION=true
GEMINI_CLASSIFICATION_TIMEOUT_SECONDS=8
```

Safe defaults keep Gemini classification disabled unless explicitly enabled.

## Structured Output Contract

Gemini must return JSON validated as:

- `difficulty`
- `primary_topic`
- `primary_pattern`
- `sub_patterns`
- `prerequisites`
- `reasoning`
- `confidence`
- `evidence`
- `risk_notes`

Invalid JSON, invalid schema, timeouts, missing API key, or runtime failures all preserve deterministic fallback.

## Response Additions

Analyze Problem responses now include:

- `classification_source`: `deterministic` or `gemini`
- `classification_adjudication`: deterministic result summary, risk decision, fallback reason, and Gemini result summary when used

## Verification

Focused tests:

```text
12 passed
```

Covered behavior:

- Risk detector flags weighted interval ambiguity
- Adjudicator uses Gemini when enabled and schema-valid
- Adjudicator falls back when Gemini classification is disabled
- Analyze endpoint can return Gemini-adjudicated classification using a fake invoker

## Known Limitations

- CI tests mock Gemini and do not call the live API.
- Gemini is only wired into Analyze Problem classification, not hints, review, planner, mock interview, or pattern transfer.
- The route is not a broad ADK multi-agent expansion.
- Gemini output quality still depends on the provided problem statement and API availability.
