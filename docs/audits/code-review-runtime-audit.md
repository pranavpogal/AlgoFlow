# Code Review Runtime Audit

Status: Completed for Phase 4B
Date: 2026-07-05

## Current Route Path

Runtime code review enters through:

```text
frontend/src/app/code-review/page.tsx::submit
  -> frontend/src/lib/api.ts::apiPost('/code-review')
  -> backend/app/api/routes.py::code_review
  -> backend/app/services/mentor_service.py::MentorService.review_code
```

Before Phase 4B, `MentorService.review_code` called `backend/app/tools/code_review.py::review_code_heuristics` directly and shaped the returned dictionary into `CodeReviewResponse`.

## Request Schema

Request schema:

- `backend/app/schemas/mentor.py::CodeReviewRequest`

Fields before Phase 4B:

- `user_id`
- `title`
- `language`
- `code`
- `problem_description`

Phase 4B adds:

- `user_intent`

Identity is resolved from `backend/app/core/auth.py::get_principal`; request-body `user_id` is not trusted by the route.

## Response Schema

Response schema:

- `backend/app/schemas/mentor.py::CodeReviewResponse`

Before Phase 4B, it returned prose/list fields only:

- correctness
- time complexity
- space complexity
- edge cases
- optimization opportunities
- readability feedback
- alternative approaches
- suspected mistakes
- senior engineer summary

Phase 4B keeps those fields and adds structured review evidence:

- review intent
- language support flag
- analysis layers
- typed findings
- corrected code when explicitly allowed
- rewrite policy flag
- unsupported claims

## Heuristic Logic Found

Legacy heuristic logic remains in:

- `backend/app/tools/code_review.py::review_code_heuristics`

Observed behavior:

- Detects off-by-one/boundary risk using substrings like `range(len`, `i+1`, `i - 1`, `<=`.
- Detects DP initialization clarity using `dp` without `dp[0]`, `base`, or `prev`.
- Detects binary-search risk using `while left`, `while l`, or `binary`.
- Detects graph visited timing using `visited` and `graph` without `add`.
- Estimates complexity from counts of `for ` and `while `.

Limitations:

- Language-agnostic string matching.
- No parser-backed evidence.
- No typed findings.
- No user-intent distinction.
- No confidence/provenance fields.
- No line-level evidence except implied by text.
- No baseline eval before Phase 4B.

## Problem-Analysis Dependency

The current code-review route does not call `detect_problem_pattern` directly. It uses `payload.title` and `problem_description` only as review context. Phase 4B uses the problem title to contextualize selected deterministic checks, for example House Robber DP transition review.

## Learner-State Dependency

Before Phase 4B, code review did not derive learner state. Phase 4B now calls:

- `backend/app/memory/repository.py::user_memory_snapshot`
- `backend/app/memory/learner_state.py::derive_learner_state`

Learner state is used conservatively in summary wording only when confidence and weak-topic evidence exist. Unknown or low-confidence state does not create strong personalization claims.

## Learning-Event Dependency

Before Phase 4B, review wrote:

- `CodeSubmitted`
- `ReviewDelivered`
- `MisconceptionDetected`

Phase 4B adds:

- `CodeReviewRequested`
- `CodeReviewCompleted`
- `CodeFindingProduced`

`MisconceptionDetected` is now written only for medium/high severity findings with confidence >= 0.7.

## Frontend Call Path

Frontend file:

- `frontend/src/app/code-review/page.tsx`

Before Phase 4B, the form sent title, language, and code. Phase 4B adds `user_intent` so the review Skill can distinguish debugging, hinting, rewrite restrictions, and corrected-code requests.

## Persistence Behavior

Persistence currently includes:

- `remember_attempt` stores the submitted code and review payload in `problem_attempts`.
- `remember_mistakes` stores suspected mistakes for learner modeling.
- `record_learning_event` stores compact event evidence without full submitted code.
- `vector_memory.add` stores a compact review memory summary, not full code.

## Capability Classification

Validated classification:

```text
Code Review
  = Reusable Skill
  + Bounded Deterministic Workflow
  + Python AST Adapter
  + Limited Text Adapters
  + Structured Evidence
  + Typed Output Validation
  + Optional Future Model Interpretation
```

It should not be an autonomous Agent in this phase because review requires tight safety boundaries, explicit provenance, and no execution.
