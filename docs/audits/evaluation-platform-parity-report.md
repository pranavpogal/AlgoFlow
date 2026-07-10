# Evaluation Platform Migration And Parity Report

Status: Complete
Owner: AlgoFlow
Phase: Unified Evaluation Platform Consolidation

## Purpose

Demonstrate that the unified evaluation platform preserves the intended semantics of the existing evaluators while adding typed protocols, common reporting, gates, artifacts, and split support.

## Migration Strategy

Old suite runners are retained. The unified platform wraps them through capability adapters instead of replacing capability-specific evaluation logic.

## Parity Summary

| Suite | Old Case Count | Unified Case Count | Old Passed | Unified Passed | Drift |
| --- | ---: | ---: | ---: | ---: | --- |
| Progressive Hinting | 5 | 5 | 5 | 5 | None observed |
| Code Review | 16 | 16 | 16 | 16 | None observed |
| Problem Intelligence | 30 | 30 | 30 | 30 | None observed |
| Pattern Transfer | 15 | 15 | 15 | 15 | None observed |

## Progressive Hinting

Old metrics:

- `case_count`: 5
- `passed`: 5
- `failed`: 0

Unified metrics:

- `pass_rate`: 1.0
- `intervention_type_accuracy`: 1.0
- `solution_leakage_rate`: 0.0

Difference: no semantic drift. The unified adapter adds explicit gate evaluation and typed checks.

## Code Review

Old metrics:

- `case_count`: 16
- `passed`: 16
- `workflow_precision`: 0.692
- `legacy_precision`: 0.625
- `unsupported_claim_rate`: 0.0
- `intent_satisfaction_rate`: 1.0
- `rewrite_policy_compliance_rate`: 1.0
- `structured_output_validity_rate`: 1.0

Unified metrics:

- Same values as old metrics, plus `pass_rate`: 1.0.

Difference: no semantic drift. The unified adapter preserves legacy precision as baseline data.

## Problem Intelligence

Old metrics:

- `case_count`: 30
- `passed`: 30
- New primary topic accuracy: 1.0
- New pattern precision: 1.0
- New pattern recall: 1.0
- New multi-label precision: 0.417
- New multi-label recall: 1.0
- Baseline primary topic accuracy: 0.6
- Baseline pattern precision: 0.3
- Baseline pattern recall: 0.3
- Unsupported-claim rate: 0.0
- Provenance completeness: 1.0
- Structured-output validity: 1.0

Unified metrics:

- Same new metric values, plus explicit gates and typed failure categories.

Difference: no semantic drift. Baseline metrics are retained in `baseline_metrics`.

## Pattern Transfer

Old metrics:

- `case_count`: 15
- `passed`: 15
- Development recommendation relevance: 1.0
- Held-out recommendation relevance: 1.0
- Adversarial recommendation relevance: 1.0
- Baseline same-topic relevance: 0.8
- New recommendation relevance: 1.0
- New transfer type accuracy: 1.0
- New structural bridge correctness: 1.0
- Same-topic shortcut rate: 0.0
- Unsupported-claim rate: 0.0
- Provenance completeness: 1.0

Unified metrics:

- Same full-suite values.
- Split filtering verified for adversarial cases: 4 cases, 4 passed, `case_count`: 4.

Difference: no semantic drift. The unified adapter normalizes split-filtered metrics so filtered reports do not mix full-suite case counts with split-specific case counts.

## Old Runner Status

Old runners are retained and not deprecated in this phase:

- `backend/app/evaluation/hint_eval.py`
- `backend/app/evaluation/code_review_eval.py`
- `backend/app/evaluation/problem_classification_eval.py`
- `backend/app/evaluation/pattern_transfer_eval.py`

Deprecation should happen only after CI uses the unified platform and parity remains stable.
