# Evaluation Metric Catalog

Status: Current
Owner: AlgoFlow

The executable metric catalog lives in `backend/app/evaluation/core/metrics.py`. This document explains how to read and govern it.

## Metric Governance

Every metric must define:

- Metric ID.
- Human-readable name.
- Capability.
- Formula or evaluation rule.
- Valid range.
- Direction.
- Aggregation behavior.
- Missing-data behavior.
- Threshold semantics.
- Limitations.

Metric definition changes should be treated as version changes. A changed metric should not be compared to historical results without an explicit migration note.

## Current Shared Metrics

- `pass_rate`: passed cases divided by total cases.
- `unsupported_claim_rate`: fraction of outputs containing claims unsupported by available evidence.
- `provenance_completeness`: fraction of outputs with required provenance evidence.
- `structured_output_validity_rate`: fraction of outputs satisfying the suite's structured-output contract.

## Current Capability Metrics

- Hinting: `solution_leakage_rate`, `intervention_type_accuracy`.
- Code review: `workflow_precision`, `legacy_precision`, `rewrite_policy_compliance_rate`, `intent_satisfaction_rate`.
- Problem intelligence: `primary_topic_accuracy`, `pattern_precision`, `pattern_recall`, `multi_label_precision`, `multi_label_recall`.
- Pattern transfer: `recommendation_relevance`, `transfer_type_accuracy`, `structural_bridge_correctness`, `same_topic_shortcut_rate`.

## Gate Policy

Gates are explicit and separate from measurement. A metric can be reported without failing CI. Current blocking gates focus on unsafe regressions:

- No solution leakage in hinting.
- No unsupported claims in code review, problem intelligence, or pattern transfer.
- Required structured-output/provenance validity where the suite has labels.
- No same-topic shortcut behavior in pattern transfer.

## Deferred Metrics

The platform can later support Brier score, expected calibration error, Recall@K, MRR, nDCG, trajectory length, tool-call correctness, token usage, and latency. These are not claimed until supporting data and runtime traces exist.
