# Gemini Hint Adjudication Report

## Scope

Expand Gemini usage from Analyze Problem into the next safest user-facing workflow: progressive hints.

This phase does not make hints fully Gemini-driven. Deterministic hint progression remains authoritative, and Gemini can only refine hint text for risky or complex hint requests when explicitly enabled.

## Before

- Hints were generated entirely by deterministic workflow logic.
- The system selected hint level, intervention type, misconception correction, and mentor note using rules.
- The API did not expose whether hint text was deterministic or model-refined.
- Reworded or complex problems could receive generic hints such as broad state/invariant prompts.
- Gemini was used only for Analyze Problem classification adjudication.

## After

- Deterministic hint workflow still runs first.
- A hint risk detector decides whether Gemini refinement is justified.
- Gemini hints are called only when `ENABLE_GEMINI_HINTS=true` and `GOOGLE_API_KEY` is available.
- Gemini returns structured JSON validated by Pydantic.
- Gemini output is rejected if it appears to leak a solution when `reveal_solution=false`.
- Deterministic hint level, reveal policy, event tracking, and fallback behavior remain preserved.
- Hint responses now include:
  - `hint_source`
  - `hint_adjudication`

## Runtime Flow

```text
Hint request
↓
Problem classification with canonical title/number support
↓
Memory retrieval and learner-state derivation
↓
Deterministic progressive hint generation
↓
Hint risk detection
↓
If low risk: return deterministic hint
↓
If risky and Gemini hints enabled: call Gemini
↓
Validate Gemini JSON and check leakage
↓
Return Gemini-refined hint or deterministic fallback
```

## Gemini Routing Triggers

Gemini hint refinement can trigger for:

- Complex patterns such as weighted interval, LIS, Greedy, graph search, prefix sum, and binary-search-on-answer
- Ambiguous optimization wording
- User attempts that need interpretation
- Multi-turn hint context
- Generic deterministic hint text

Explicit solution requests stay on deterministic solution-level guardrails.

## Configuration

```bash
GOOGLE_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
ENABLE_GEMINI_HINTS=true
GEMINI_HINT_TIMEOUT_SECONDS=8
```

## Verification

Focused hint tests:

```text
11 passed
```

Covered behavior:

- Risk detector flags complex hint requests
- Gemini hint is used when enabled and safe
- Gemini hint falls back when disabled
- Gemini hint is rejected if it leaks solution structure
- Hint API can return a Gemini-refined hint through a fake invoker

## Known Limitations

- CI tests mock Gemini and do not call the live API.
- Gemini currently refines hint text only; it does not control hint level or reveal policy.
- The leakage guard is intentionally conservative and may reject some useful but too-specific hints.
- Code review, mock interview, recommendations, planner, and analytics remain mostly deterministic.
