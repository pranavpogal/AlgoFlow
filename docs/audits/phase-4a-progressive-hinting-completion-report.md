# Phase 4A Completion Report: Progressive Hinting Rationalization

Status: Completed
Date: 2026-07-05
Scope: Agent / Skill / Workflow rationalization for progressive hinting only

## Phase Checkpoint

Phase 4A converts progressive hinting from a static ladder into a bounded mentoring Skill plus deterministic workflow. The implementation intentionally avoids Gemini/ADK generation in this phase so behavior can be audited, tested, and evaluated before model reasoning is introduced.

## Current Hint Architecture Found

The pre-phase hint path was:

- Frontend: `frontend/src/app/hints/page.tsx`
- API route: `POST /api/v1/hints/next`
- Backend route: `backend/app/api/routes.py::next_hint`
- Service: `backend/app/services/mentor_service.py::MentorService.next_hint`
- Pattern context: `backend/app/tools/problem_tools.py::detect_problem_pattern`
- Memory context: vector snippets plus structured learner events

The previous runtime behavior used a fixed five-step ladder selected mostly by `current_hint_level`, with only light mentor-note personalization. It did not retrieve previous hint events, did not classify user intent, and did not persist structured hint decision evidence.

## Chosen Primitive Classification

Progressive hinting is classified as:

- Skill: reusable mentoring capability with its own operating rules and leakage policy.
- Workflow: deterministic state transition from context to intervention type.
- Deterministic context layer: problem pattern, learner state, previous hints, current attempt, and explicit reveal intent.
- Optional future model layer: Gemini/ADK may later be used for wording or nuanced reasoning, but only behind the same policy/eval gates.

It is not treated as a standalone autonomous Agent yet because the core behavior benefits from strict bounded disclosure, predictable escalation, and testable leakage controls.

## Architecture Decision

Decision: Implement progressive hinting as a Skill-backed deterministic workflow before connecting it to ADK/Gemini.

Justification:

- Hinting has high solution-leakage risk, so policy should be enforced outside model text generation.
- The smallest useful mentor intervention can be represented as a bounded taxonomy.
- Deterministic behavior enables regression tests and eval cases before adding model variability.
- This preserves the whitepaper principle of making AI behavior inspectable, measurable, and incrementally promotable.

## Implemented Intervention Taxonomy

The workflow supports the bounded intervention set required by the phase prompt:

- `IDEA_VALIDATION`
- `REFLECTIVE_QUESTION`
- `CONCEPTUAL_NUDGE`
- `MISCONCEPTION_CORRECTION`
- `STATE_DEFINITION_PROMPT`
- `INVARIANT_PROMPT`
- `EDGE_CASE_PROMPT`
- `COUNTEREXAMPLE`
- `COMPLEXITY_CHALLENGE`
- `PARTIAL_PSEUDOCODE`
- `EXPLICIT_SOLUTION`

## User Intent Handling

The workflow now detects intent from the user attempt and explicit reveal flag:

- Validate my idea
- Give one hint
- Give another hint
- Explain why my state is wrong
- Do not give the solution
- Reveal the full solution
- Code request
- Approach review
- I already know the recurrence

User intent dominates escalation. For example, `do not give the solution` prevents solution-level output even if the prompt contains implementation-related language, while explicit reveal intent permits `EXPLICIT_SOLUTION`.

## Previous-Hint Awareness

The backend now retrieves previous `HintDelivered` learning events for the same user and problem title, extracts prior intervention types, and avoids repeating the same intervention when a smaller next step is available.

When the workflow detects a repeated candidate intervention and moves forward, it records `HintEscalated` with evidence explaining that it avoided repeating the previous hint.

## Learner-State Integration

Hinting now derives learner state from structured learning events before selecting a response.

Current usage:

- Reads learner-state confidence.
- Uses weak-topic evidence only when confidence is not `unknown`.
- Keeps mentor notes conservative for cold-start users.
- Persists learner-state confidence in `HintDelivered` evidence.

This keeps personalization evidence-based instead of inventing weaknesses for new users.

## Learning-Event Integration

New or expanded event behavior:

- `HintRequested`: recorded before hint generation.
- `HintDelivered`: records structured decision evidence.
- `HintEscalated`: recorded when the workflow avoids repeating a previous intervention.
- `MisconceptionAddressed`: recorded when a misconception-specific correction is delivered.

`HintDelivered` evidence includes:

- hint level
- intervention type
- detected intent
- reveal flag
- user-attempt presence
- requested reveal flag
- learner-state confidence
- detected misconception
- previous-hint context usage
- solution leakage risk
- next escalation condition

## Files Created

- `backend/app/skills/__init__.py`
- `backend/app/skills/progressive_hinting/__init__.py`
- `backend/app/skills/progressive_hinting/SKILL.md`
- `backend/app/skills/progressive_hinting/workflow.py`
- `backend/app/evaluation/__init__.py`
- `backend/app/evaluation/hint_eval.py`
- `backend/tests/test_progressive_hinting_skill.py`
- `backend/tests/test_hint_eval.py`
- `docs/audits/progressive-hinting-audit.md`
- `docs/audits/phase-4a-progressive-hinting-completion-report.md`
- `evals/hint_leakage/cases.jsonl`

## Files Modified

- `backend/app/services/mentor_service.py`
- `specs/features/adaptive-hinting.md`

## Static Ladder Status

The old fixed service-level hint ladder has been removed from runtime selection. The system now chooses an intervention based on intent, misconception signals, current level, problem pattern, learner state, and previous hint events.

Some deterministic templates remain by design, but they are selected through a state-aware workflow rather than a hard-coded linear ladder.

## Model Integration Status

Gemini/ADK model reasoning was not integrated in this phase.

Current fallback behavior is deterministic and local. This is intentional because the phase objective is workflow rationalization, leakage control, and testability before introducing model variability.

## Evaluation Cases Added

Added five deterministic hint leakage cases in `evals/hint_leakage/cases.jsonl`:

- DP first hint should not reveal solution.
- Idea validation should validate without jumping ahead.
- Wrong DP state should trigger misconception correction.
- Explicit solution request may reveal solution-level guidance.
- Previous state-definition hint should escalate rather than repeat.

## Verification Results

Commands run:

```bash
cd backend && .venv/bin/pytest -q
cd backend && .venv/bin/ruff check app tests
cd frontend && npm run build
```

Results:

- Backend tests: 23 passed, 1 warning.
- Backend lint: passed.
- Frontend production build: passed.
- Hint eval: 5 cases, 5 passed, 0 failed.

## Known Limitations

- Hint wording is still deterministic template text.
- No Gemini/ADK model call is used for adaptive hint generation yet.
- Previous-hint context is inferred from user plus problem title, not an explicit hint-session id.
- The frontend still provides a limited hint workspace and does not expose all internal structured fields.
- The current hint request schema does not include full user code, so code-aware hinting remains out of scope.
- The eval suite is intentionally small and should be expanded before production rollout.
- There is no centralized Skill registry or policy gateway for all mentoring workflows yet.

## Next Recommended Phase

Continue the same rationalization approach with the Code Review workflow:

- Audit current review path.
- Classify review as Skill, Workflow, Agent, or Tool combination.
- Add structured review dimensions and severity taxonomy.
- Persist review evidence into learner events.
- Add eval cases for correctness, complexity, edge-case detection, and non-hallucination.

Do not proceed automatically beyond this checkpoint without approval.
