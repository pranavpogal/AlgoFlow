# Phase 4C Completion Report: Problem Classification / Topic Detection Rationalization

Status: Completed
Date: 2026-07-06
Scope: Problem classification and topic detection only

## Phase Checkpoint

Phase 4C transforms problem analysis from curated keyword heuristics into a bounded Problem Intelligence Skill plus deterministic workflow with typed taxonomy, evidence extraction, confidence calibration, provenance, tests, and evaluations.

No Gemini classifier was added. No decorative specialist agent was added. Recommendation and Pattern Transfer work were not expanded.

## Current Classification Architecture Found

Audited path:

```text
frontend/src/app/problem-analysis/page.tsx::submit
  -> frontend/src/lib/api.ts::apiPost('/problems/analyze')
  -> backend/app/api/routes.py::analyze_problem
  -> backend/app/services/mentor_service.py::MentorService.analyze_problem
  -> backend/app/tools/problem_intelligence.py::detect_problem_pattern
```

The full audit is documented in `docs/audits/problem-classification-runtime-audit.md`.

## Chosen Primitive Classification

Validated classification:

- Skill: reusable Problem Intelligence capability with activation and safety rules.
- Workflow: deterministic evidence-to-taxonomy pipeline.
- Typed taxonomy: separate topics, patterns, subpatterns, structural cues, prerequisites, and related patterns.
- Evidence extraction: observed prompt evidence with inferred labels.
- Confidence calibration: high for curated metadata, lower for ambiguous/multi-label cases.
- Optional model classification: deferred.
- Structured output validation: response schema and eval checks.

Problem classification is not an autonomous Agent in this phase.

## Taxonomy Created

Phase 4C defines explicit distinctions:

- Topic: broad DSA area, for example Dynamic Programming.
- Pattern: concrete solving strategy, for example LIS-style DP.
- Subpattern: narrower implementation shape, for example Path Reconstruction.
- Structural cue: observed prompt evidence, for example best chain ending at each index.
- Prerequisite concept: required prior knowledge, for example Sorting.
- Related pattern: nearby transfer idea, for example Knapsack DP.

Implemented taxonomy version:

- `problem-intelligence-taxonomy-v1`

## Files Created

- `backend/app/skills/problem_intelligence/__init__.py`
- `backend/app/skills/problem_intelligence/SKILL.md`
- `backend/app/skills/problem_intelligence/workflow.py`
- `backend/app/evaluation/problem_classification_eval.py`
- `backend/tests/test_problem_intelligence_skill.py`
- `backend/tests/test_problem_classification_eval.py`
- `docs/audits/problem-classification-runtime-audit.md`
- `docs/audits/phase-4c-problem-classification-completion-report.md`
- `specs/features/problem-intelligence.md`
- `evals/problem_classification/cases.jsonl`

## Files Modified

- `backend/app/tools/problem_intelligence.py`
- `backend/app/schemas/mentor.py`
- `backend/app/services/mentor_service.py`
- `docs/API.md`

## Old Heuristics Removed or Retained

Removed from the primary runtime path:

- The old broad keyword counter no longer directly powers `detect_problem_pattern`.

Retained as a baseline:

- `backend/app/skills/problem_intelligence/workflow.py::legacy_detect_problem_pattern`

Reason:

- Phase 4C requires measured comparison against the current heuristic baseline.

## Evidence Sources

Current evidence sources:

- `CURATED_METADATA` for known canonical problems.
- `TITLE_HEURISTIC` for title phrase matches.
- `STATEMENT_EVIDENCE` for description phrase matches.
- `CONSTRAINT_EVIDENCE` when constraint-like markers appear in the statement.
- `STRUCTURAL_RULE` reserved for future richer structural parsing.
- `MODEL_INFERENCE` reserved for future Gemini/ADK classification.

Current runtime receives title and description only. It does not receive trusted external tags, examples, or parsed constraints as separate fields.

## Confidence Behavior

- Curated canonical metadata: high confidence around 0.96.
- Strong structural phrase evidence: medium/high confidence depending on evidence count and separation.
- Ambiguous multi-label problems: secondary topics are preserved and confidence remains bounded.
- Fallback: low confidence 0.35 with unsupported-claim note.

## Learner-State Integration

Classification output is stored as exposure/classification evidence only.

Rules enforced:

- Seeing a DP problem does not imply DP mastery.
- `ProblemClassified`, `PatternDetected`, and `StructuralCueDetected` events include `mastery_evidence: false`.
- Existing learner-state exposure counts remain weaker than review/interview/mistake evidence.

## Learning-Event Integration

Events now include:

- `ProblemClassified`
- `PatternDetected`
- `StructuralCueDetected`

Noise control:

- `PatternDetected` is emitted only when confidence is at least 0.7.
- Structural cue events are capped to the first three cues.
- Events carry classification-only/mastery-false evidence.

## Downstream Contract Changes

Backward-compatible fields are preserved:

- `pattern`
- `sub_patterns`
- `prerequisites`
- `reasoning`

New fields are available for safer downstream use:

- `primary_topic`
- `secondary_topics`
- `primary_pattern`
- `structural_cues`
- `related_patterns`
- `difficulty_signals`
- `confidence`
- `evidence`
- `provenance`
- `unsupported_claims`
- `taxonomy_version`

Current downstream consumers still mostly use the legacy broad `pattern` field. Future phases should migrate hinting, recommendations, and Pattern Transfer toward stable taxonomy identifiers.

## Model Integration

No Gemini/ADK model call was added.

This is intentional. Deterministic evidence, taxonomy validation, and eval baselines now exist before any model-assisted classifier is introduced.

## Fallback Behavior

If no strong evidence matches:

- primary topic: `General Problem Solving`
- primary pattern: `General Reasoning`
- confidence: `0.35`
- unsupported claim: insufficient structural evidence for high-confidence classification

## Evaluation Dataset

Dataset path:

- `evals/problem_classification/cases.jsonl`

Dataset size:

- 30 cases

Coverage includes:

- arrays / hashing
- two pointers
- sliding window
- binary search
- binary search on answer
- stacks
- monotonic stack
- linked lists
- trees
- BST
- graphs
- BFS
- DFS
- shortest paths
- topological sorting
- union find
- greedy
- intervals
- dynamic programming
- knapsack
- LIS
- LCS
- interval DP
- digit DP
- bit manipulation
- prefix sums
- backtracking
- tries
- ambiguous and multi-label problems

## Baseline Metrics

Legacy baseline on the 30-case eval set:

- Primary-topic accuracy: 0.600
- Pattern precision: 0.300
- Pattern recall: 0.300
- Multi-label precision: 0.000
- Multi-label recall: 0.000

## New Metrics

Phase 4C workflow on the 30-case eval set:

- Primary-topic accuracy: 1.000
- Pattern precision: 1.000
- Pattern recall: 1.000
- Multi-label precision: 0.417
- Multi-label recall: 1.000
- Unsupported-claim rate: 0.000
- Provenance completeness rate: 1.000
- Structured-output validity rate: 1.000

## Calibration Findings

- Explicit ambiguous-case count: 2
- Overconfident ambiguous cases: 0

Important caveat:

- Multi-label precision is intentionally modest at 0.417. The deterministic classifier currently preserves extra plausible secondary topics rather than hiding uncertainty.

## Tests Run

Commands:

```bash
cd backend && .venv/bin/pytest -q
cd backend && .venv/bin/ruff check app tests
cd frontend && npm run build
```

Results before final frontend build:

- Backend tests: 34 passed, 1 warning.
- Backend lint: passed.
- Frontend build: passed.

Final verification completed successfully.

## Known Limitations

- The taxonomy is useful but still hand-built and incomplete.
- Multi-label precision needs improvement before recommendation and Pattern Transfer depend on it heavily.
- Current runtime receives only title and description, not separately parsed constraints/examples/tags.
- Some evidence is phrase-based, not deep semantic parsing.
- Stable taxonomy IDs are internal; public response still primarily exposes labels.
- Hinting, recommendations, and Pattern Transfer still consume the broad legacy `pattern` field.
- No Gemini/ADK model classifier is integrated.
- No external problem metadata ingestion exists.

## Next Recommended Phase

Recommended next controlled phase:

1. Pattern Recommendation / Pattern Transfer rationalization, now that classification has a taxonomy foundation.
2. Or Evaluation Platform consolidation, so hint/code-review/classification eval metrics share one reporting interface.

Do not proceed beyond this checkpoint without approval.
