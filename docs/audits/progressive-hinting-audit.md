# Progressive Hinting Runtime Audit

Date: 2026-07-05

## Current Runtime Path

Frontend call path:

- `frontend/src/app/hints/page.tsx::next` calls `apiPost('/hints/next')`.
- The frontend sends hardcoded `user_id`, `title`, `description`, `current_hint_level`, and `reveal_solution`.
- It stores returned `level` in React state and renders the raw JSON response.

API route:

- `backend/app/api/routes.py::next_hint` handles `POST /api/v1/hints/next`.
- It accepts `HintRequest` and resolves `Principal` through `get_principal`.
- It passes `principal.user_id` to the service.

Request schema:

- `backend/app/schemas/mentor.py::HintRequest` extends `ProblemInput`.
- Fields: `user_id`, `problem_number`, `title`, `url`, `description`, `current_hint_level`, `user_attempt`, `reveal_solution`.
- No current code field, session ID, explicit intent enum, or previous hint IDs.

Service method:

- `backend/app/services/mentor_service.py::MentorService.next_hint` is the true runtime implementation.
- It calls `user_memory_snapshot(session, user_id)`.
- It calls `detect_problem_pattern(payload.title, payload.description)`.
- It reads static profile weak topics from `memory['profile']` rather than derived learner state.
- It computes `level = 5` if `reveal_solution` is true, otherwise increments `current_hint_level`.
- It selects from a static five-step `hint_ladder`.
- It returns `HintResponse`.

Current five-step ladder:

1. choice identification
2. state definition
3. recurrence in words
4. base-case testing
5. solution reveal

Problem-analysis dependency:

- Uses `backend/app/tools/problem_intelligence.py::detect_problem_pattern` directly.
- This is deterministic curated/keyword classification, not ADK/Gemini.

Learner-state dependency:

- Uses `backend/app/memory/repository.py::user_memory_snapshot`.
- Does not currently call `derive_learner_state` in hinting.
- Therefore Phase 6 evidence-derived confidence is not used by hints yet.

Learning-event dependency:

- Current hinting records `HintDelivered` through `record_learning_event`.
- No `HintRequested`, `HintEscalated`, `HintRepeated`, or `MisconceptionAddressed` events exist yet.
- Previous hints are not retrieved from events.

Memory dependency:

- Uses relational memory snapshot.
- Does not use `VectorMemory.search`.
- Does not retrieve previous hint text from durable memory.

Persistence behavior:

- Writes `HintDelivered` with level, reveal flag, user attempt presence, and requested reveal flag.
- Does not persist session ID.
- Does not record intervention type, intent, leakage risk, previous-hint usage, or escalation condition.

## Primitive Classification

Progressive hinting should be implemented as:

```text
Reusable Skill
  + Bounded Workflow
  + Deterministic Context Construction
  + Structured Output Validation
  + Optional Model Reasoning Later
```

## Justification

Not an autonomous agent right now because:

- It does not require independent lifecycle ownership.
- It does not require separate deployment.
- It should not autonomously replan across broad tools.
- It has a bounded procedure: classify intent, construct context, select intervention, enforce leakage policy, record evidence.

Not merely a tool because:

- It encodes tutoring procedure, not just external access or a deterministic lookup.
- It must preserve learner intent and progressive disclosure.

Not purely deterministic service forever because:

- Later versions may benefit from model wording and semantic misconception interpretation.
- However, deterministic policy and structured output should remain the safety boundary.

## Immediate Decision

Implement a deterministic progressive-hinting Skill/workflow first. Do not connect ADK/Gemini in this phase. Model integration should wait until evals and leakage tests are in place and stable.
