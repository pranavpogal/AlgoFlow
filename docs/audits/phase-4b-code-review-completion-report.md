# Phase 4B Completion Report: Code Review Skill / Workflow Rationalization

Status: Completed
Date: 2026-07-05
Scope: Code review only

## Phase Checkpoint

Phase 4B transforms code review from loose string heuristics into a bounded Code Review Skill plus deterministic workflow with typed findings, explicit evidence, confidence, provenance, intent handling, conservative learner-state use, tests, and evaluations.

No learner code execution was added.

## Current Code-Review Architecture Found

Audited path:

```text
frontend/src/app/code-review/page.tsx::submit
  -> apiPost('/code-review')
  -> backend/app/api/routes.py::code_review
  -> backend/app/services/mentor_service.py::MentorService.review_code
  -> previously backend/app/tools/code_review.py::review_code_heuristics
```

The full audit is documented in `docs/audits/code-review-runtime-audit.md`.

## Chosen Primitive Classification

Validated classification:

- Skill: reusable code-review mentoring behavior with activation and safety rules.
- Workflow: deterministic review pipeline with typed outputs.
- Language-specific adapters: Python AST support now; limited text adapters for selected languages.
- Structured evidence model: findings include evidence, confidence, provenance, and location.
- Optional future model interpretation: deferred until eval gates and policy boundaries exist.

Code review is not promoted to a live autonomous Agent in this phase.

## Architecture Decision

Decision: Implement code review as a Skill-backed deterministic workflow with safe static analysis layers.

Justification:

- Submitted code is untrusted and must not be executed in FastAPI or ADK runtime.
- Review findings need auditable evidence and confidence.
- Intent handling affects whether the mentor gives a hint, bug explanation, improvement suggestions, or corrected code.
- Python AST parsing can provide truthful structural evidence without execution.
- Other languages should degrade honestly until adapters exist.

## Files Created

- `backend/app/skills/code_review/__init__.py`
- `backend/app/skills/code_review/SKILL.md`
- `backend/app/skills/code_review/workflow.py`
- `backend/app/evaluation/code_review_eval.py`
- `backend/tests/test_code_review_skill.py`
- `backend/tests/test_code_review_eval.py`
- `docs/audits/code-review-runtime-audit.md`
- `docs/audits/phase-4b-code-review-completion-report.md`
- `evals/code_review/cases.jsonl`

## Files Modified

- `backend/app/schemas/mentor.py`
- `backend/app/services/mentor_service.py`
- `frontend/src/app/code-review/page.tsx`
- `backend/tests/test_progressive_hinting_skill.py`
- `specs/features/code-intelligence.md`
- `docs/API.md`

## Old String Heuristics Removed or Retained

Retained as legacy baseline:

- `backend/app/tools/code_review.py::review_code_heuristics`

Removed from primary runtime path:

- `MentorService.review_code` no longer calls the legacy heuristic directly.

Reason for retaining:

- Provides measured baseline comparison for Phase 4B evals.
- Still referenced by older ADK scaffold/tool definitions that are not the primary runtime path.

## Supported Languages

Current support:

- Python: parser-backed AST parse, selected AST/static patterns, and structural text checks.
- Java, C++, JavaScript, TypeScript, Go: limited text-pattern review only.
- Other languages: unsupported-language finding with honest degradation.

No language has execution-backed correctness claims.

## Analysis Layers Implemented

Current layers:

1. Request/intent analysis.
2. Language detection.
3. Python AST parse.
4. Python AST pattern checks.
5. Limited structural text checks.
6. Skill-based pedagogical interpretation.
7. Pydantic response validation through `CodeReviewResponse` and `CodeFinding`.

Deferred layers:

- Secure execution evidence.
- Test-failure evidence.
- Counterexample evidence.
- Dynamic complexity evidence.
- LLM/Gemini semantic interpretation.

## Intent Handling Implemented

The workflow distinguishes:

- `REVIEW_CODE`
- `FIND_BUG`
- `ONE_HINT`
- `EXPLAIN_FAILURE`
- `ANALYZE_COMPLEXITY`
- `SUGGEST_IMPROVEMENTS`
- `DO_NOT_REWRITE`
- `PROVIDE_CORRECTED_CODE`
- `COMPARE_APPROACHES`

Rewrite behavior:

- Corrected code is only returned for explicit corrected-code intent.
- `ONE_HINT` and `DO_NOT_REWRITE` preserve learner ownership and avoid replacement solutions.

## Evidence Model Implemented

Each finding includes:

- `finding_id`
- `category`
- `severity`
- `confidence`
- `evidence_type`
- `evidence`
- `location.line_start`
- `location.line_end`
- `message`
- `pedagogical_action`
- `provenance`

Line locations are included only when parser/AST evidence can support them.

## Learner-State Integration

Phase 4B uses Phase 6 learner intelligence conservatively:

- Unknown state remains unknown.
- Weak-topic personalization is used only when learner confidence is medium/high.
- Learner state affects summary wording, not deterministic finding creation.
- Findings become learner evidence only with explicit confidence and provenance.

## Learning-Event Integration

Events now include:

- `CodeReviewRequested`
- `CodeSubmitted`
- `ReviewDelivered`
- `CodeReviewCompleted`
- `CodeFindingProduced`
- `MisconceptionDetected`

Noise control:

- `MisconceptionDetected` is emitted only for medium/high severity findings with confidence >= 0.7.
- Full code is not stored inside learning-event evidence.

## Model Integration

No Gemini/ADK model call was added in Phase 4B.

This is intentional. The current workflow is deterministic, auditable, and eval-tested before model interpretation is introduced.

## Fallback Behavior

- Unsupported language: returns an `unsupported_language` finding and avoids structural correctness claims.
- Non-Python supported-list languages: limited text-pattern review only.
- Python syntax error: stops at syntax finding rather than pretending deeper analysis is valid.
- No deterministic issue found: returns an info-level correctness finding and states correctness is not proven.

## Evaluation Cases Added

Added 16 cases in `evals/code_review/cases.jsonl`:

- correct code
- syntax issue
- off-by-one error
- wrong boundary
- integer overflow risk
- incorrect DP transition
- incorrect base case
- binary-search invariant error
- graph visited-state error
- mutation-during-iteration issue
- complexity concern
- ambiguous code
- unsupported language
- one-hint request
- rewritten-code forbidden
- corrected-code requested

## Evaluation Results

Eval command:

```bash
cd backend
.venv/bin/python - <<'PY'
from app.evaluation.code_review_eval import evaluate_code_review_cases
print(evaluate_code_review_cases('../evals/code_review/cases.jsonl'))
PY
```

Summary:

- Cases: 16
- Passed: 16
- Failed: 0
- Workflow precision: 0.692
- Legacy precision: 0.625
- Unsupported-claim rate: 0.0
- Intent satisfaction rate: 1.0
- Rewrite-policy compliance rate: 1.0
- Structured-output validity rate: 1.0

## Unsupported-Claim Findings

No unsupported-claim violations were found in the Phase 4B eval set.

The workflow explicitly reports that:

- no learner code was executed;
- non-Python languages do not receive AST-backed claims;
- correctness is evidence-limited without tests/execution.

## Tests Run

Commands:

```bash
cd backend && .venv/bin/pytest -q
cd backend && .venv/bin/ruff check app tests
cd frontend && npm run build
```

Results before final frontend build:

- Backend tests: 29 passed, 1 warning.
- Backend lint: passed.
- Frontend build: passed.

Final verification completed successfully.

## Known Limitations

- Python AST checks are targeted, not comprehensive static analysis.
- Java, C++, JavaScript, TypeScript, and Go only have limited text-pattern review.
- No secure execution sandbox exists.
- No test-runner or counterexample engine exists.
- No Gemini/ADK semantic interpretation is used yet.
- Corrected-code generation is currently a small guarded Python House Robber stub, not a general repair system.
- Eval precision is measured on a small local fixture set and should not be treated as production quality.
- Existing `problem_attempts` still stores submitted code; learning events avoid full-code storage.

## Next Recommended Phase

Continue Phase 4 rationalization with one of:

1. Topic Detection / Problem Classification Skill rationalization.
2. Pattern Recommendation / Pattern Transfer Skill rationalization.
3. Expand evaluation platform with shared metrics output and CI gating.

Do not proceed beyond this checkpoint without approval.
