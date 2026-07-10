# Problem Classification Runtime Audit

Status: Completed for Phase 4C
Date: 2026-07-06

## Current Route Path

Problem analysis enters through:

```text
frontend/src/app/problem-analysis/page.tsx::submit
  -> frontend/src/lib/api.ts::apiPost('/problems/analyze')
  -> backend/app/api/routes.py::analyze_problem
  -> backend/app/services/mentor_service.py::MentorService.analyze_problem
  -> backend/app/tools/problem_intelligence.py::detect_problem_pattern
```

Before Phase 4C, `detect_problem_pattern` used curated overrides for a small number of canonical problems and then counted keyword matches across broad pattern labels.

## Request Schema

Request schema:

- `backend/app/schemas/mentor.py::ProblemInput`

Fields:

- `user_id`, ignored for ownership by write routes
- `problem_number`
- `title`
- `url`
- `description`

The system currently receives title and statement text. It does not receive trusted LeetCode tags, parsed constraints, parsed examples, or known metadata except internal curated canonical-problem metadata.

## Response Schema

Response schema:

- `backend/app/schemas/mentor.py::TopicAnalysis`

Before Phase 4C, the response exposed:

- problem
- difficulty
- pattern
- sub_patterns
- prerequisites
- reasoning

Phase 4C keeps those fields and adds:

- primary topic
- secondary topics
- primary pattern
- structural cues
- related patterns
- difficulty signals
- confidence
- evidence
- provenance
- unsupported claims
- taxonomy version

## Heuristic Logic Found

Legacy logic previously lived in:

- `backend/app/tools/problem_intelligence.py::detect_problem_pattern`

Observed behavior before Phase 4C:

- Curated overrides for `Largest Divisible Subset` and `House Robber`.
- Keyword maps for broad labels such as Dynamic Programming, Graphs, Sliding Window, Binary Search, Trees, Backtracking, Greedy, and Hash Maps.
- One highest-count label selected as `pattern`.
- Subpatterns and prerequisites were selected from broad static dictionaries.
- Reasoning was generic and did not include evidence/provenance.

Phase 4C retains a legacy baseline as:

- `backend/app/skills/problem_intelligence/workflow.py::legacy_detect_problem_pattern`

## Topic Labels and Pattern Labels

Before Phase 4C, labels were collapsed into a single free-form `pattern` string.

Phase 4C separates:

- Topic: broad knowledge area, for example Dynamic Programming.
- Pattern: concrete problem-solving strategy, for example LIS-style DP.
- Subpattern: narrower implementation shape, for example Path Reconstruction.
- Structural cue: observed evidence in the prompt, for example best chain ending at each index.
- Prerequisite concept: required prior knowledge, for example Sorting.
- Related pattern: nearby pattern useful for future transfer, for example Knapsack DP.

## Downstream Consumers

Current consumers of classification:

- `MentorService.analyze_problem`: persists attempts and classification events.
- `MentorService.next_hint`: uses detected broad topic/pattern string for progressive hinting.
- `MentorService.recommendations`: uses detected broad topic string for static related problems.
- `MentorService.pattern_transfer`: uses detected broad topic string for transfer scaffold.
- `remember_attempt`: stores `ProblemAttempt.pattern` as exposure evidence.
- `derive_learner_state`: uses pattern exposure counts conservatively, but exposure is weaker than solve/review evidence.
- Frontend problem analysis page displays the full JSON response.

## Learning Events

Before Phase 4C, analysis wrote:

- `ProblemClassified`

Phase 4C adds bounded evidence events:

- `PatternDetected`
- `StructuralCueDetected`

These events explicitly set `mastery_evidence` to false so classification does not imply learner competence.

## Capability Classification

Validated classification:

```text
Problem Intelligence
  = Reusable Skill
  + Bounded Deterministic Workflow
  + Typed Taxonomy
  + Evidence Extraction
  + Confidence Calibration
  + Optional Future Model Classification
  + Structured Output Validation
```

It is not a decorative specialist Agent in this phase.
