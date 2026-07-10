# Pattern Recommendation / Transfer Runtime Audit

Status: Completed for Phase 4D
Date: 2026-07-06

## Current Runtime Paths Found

Problem recommendations:

```text
backend/app/api/routes.py::recommendations
  -> backend/app/services/mentor_service.py::MentorService.recommendations
  -> previously backend/app/tools/problem_intelligence.py::recommend_related_problems
```

Pattern transfer:

```text
backend/app/api/routes.py::pattern_transfer
  -> backend/app/services/mentor_service.py::MentorService.pattern_transfer
  -> previously backend/app/tools/problem_intelligence.py::recommend_related_problems
```

Study planning recommendations:

```text
backend/app/api/routes.py::study_plan
  -> backend/app/services/mentor_service.py::MentorService.study_plan
  -> backend/app/tools/learning_tools.py::build_weekly_plan
```

Learner analytics recommendations:

```text
backend/app/api/routes.py::analytics
  -> backend/app/services/mentor_service.py::MentorService.analytics
  -> backend/app/memory/learner_state.py::derive_learner_state
  -> backend/app/memory/learner_state.py::_recommendations
```

Frontend recommendation display:

- No dedicated recommendations page exists.
- `frontend/src/app/analytics/page.tsx` defines a `recommendations` field but currently does not render the list.
- `frontend/src/app/study-planner/page.tsx` renders weekly study-plan activities, not pattern transfer.

## Schemas

Request schema:

- `backend/app/schemas/mentor.py::ProblemInput`

Response schemas:

- `backend/app/schemas/mentor.py::RecommendationResponse`
- `backend/app/schemas/mentor.py::PatternTransferResponse`

## Current Problems Identified

Before Phase 4D:

- `recommend_related_problems` returned static lists by broad topic string.
- `/recommendations` and `/pattern-transfer` were not learner-scoped by principal.
- Pattern transfer text was a generic scaffold, not evidence-backed transfer reasoning.
- Study planning used weak-topic strings and static loops.
- Learner analytics returned simple recommendation strings based on derived weak topics/mistakes.
- No transfer taxonomy existed.
- No structural relationship model existed.
- No transfer eval existed.
- Recommendations could confuse problem exposure with learning progress if downstream consumers overread attempts.

## Capability Classification

Validated classification:

```text
Pattern Transfer
  = Reusable Pattern Transfer Skill
  + Bounded Deterministic Workflow
  + Problem Intelligence Taxonomy
  + Structural Relationship Model
  + Evidence-Derived Learner State
  + Confidence-Aware Decision Policy
  + Explainable Recommendation Output
  + Optional Future Model Reasoning
  + Typed Output Validation
```

No autonomous PatternTransferAgent is justified in Phase 4D.

## Whitepaper Alignment

The implementation follows:

- Least autonomous primitive from `docs/whitepaper-engineering-principles/01-agentic-engineering-principles.md`.
- Skill/workflow boundary from `docs/whitepaper-engineering-principles/03-agent-skills-principles.md`.
- Eval-first and user-scoped evidence guidance from `docs/whitepaper-engineering-principles/04-security-evaluation-principles.md`.
- ADR boundary in `docs/adr/0001-agent-skill-workflow-boundaries.md`.

## Persistence Behavior

Phase 4D writes:

- `PatternTransferRequested`
- `PatternTransferRecommended`

These events are user-scoped and explicitly carry `mastery_evidence: false`.

A recommendation being shown is not evidence of mastery.
