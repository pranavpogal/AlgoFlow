# Evaluation Platform Runtime Audit

Status: Completed for Unified Evaluation Platform phase
Date: 2026-07-06

## Existing Evaluation Paths

### Progressive Hinting

- Runner: `backend/app/evaluation/hint_eval.py::evaluate_hint_cases`
- Cases: `evals/hint_leakage/cases.jsonl`
- Capability: Progressive Hinting Skill/workflow
- Dataset format: JSONL, one case per line
- Case schema: `case_id`, `suite`, `input`, `expected_behavior`, `forbidden_behavior`, `expected_intervention`, `tags`
- Metrics: case count, passed count, failed list, per-case `intervention_ok`, `leakage_ok`
- Pass/fail semantics: intervention must match expected intervention and no forbidden solution marker may appear unless solution reveal is allowed
- Threshold semantics: implicit all cases should pass; no explicit gates
- Baseline support: none
- Split support: none
- Output format: ad hoc dictionary
- Reproducibility: deterministic workflow, local JSONL, no model calls
- Failure behavior: malformed cases raise Python exceptions; assertion failures are represented only as failed cases
- CI compatibility: usable from pytest but no standalone CLI or exit-code contract
- Known limitations: marker-based leakage detection is narrow; no helpfulness scoring; no latency or trace metadata

### Code Review

- Runner: `backend/app/evaluation/code_review_eval.py::evaluate_code_review_cases`
- Cases: `evals/code_review/cases.jsonl`
- Capability: Code Review Skill/workflow
- Dataset format: JSONL
- Case schema: title, language, user intent, code, expected categories, forbidden categories, rewrite expectation, optional summary substring
- Metrics: workflow precision, legacy precision, unsupported-claim rate, intent-satisfaction rate, rewrite-policy compliance, structured-output validity
- Pass/fail semantics: expected categories subset detected categories, forbidden categories absent, rewrite policy satisfied, intent text satisfied, structured findings valid, unsupported claims controlled
- Threshold semantics: implicit all cases should pass; no explicit gates
- Baseline support: legacy `review_code_heuristics` precision
- Split support: none
- Output format: ad hoc dictionary
- Reproducibility: deterministic, no model calls, no code execution
- Failure behavior: malformed cases raise Python exceptions
- CI compatibility: pytest wrapper exists; no unified CLI
- Known limitations: precision is approximate because labels are coarse; recall is limited by available labels

### Problem Intelligence / Classification

- Runner: `backend/app/evaluation/problem_classification_eval.py::evaluate_problem_classification_cases`
- Cases: `evals/problem_classification/cases.jsonl`
- Capability: Problem Intelligence Skill/workflow
- Dataset format: JSONL
- Case schema: title, description, expected primary topic, expected primary pattern, expected secondary topics, optional max confidence
- Metrics: primary-topic accuracy, pattern precision/recall, multi-label precision/recall, unsupported-claim rate, provenance completeness, structured-output validity, calibration findings
- Pass/fail semantics: primary topic/pattern match, expected secondary topics included, confidence within max when specified, provenance and structure valid, unsupported claims controlled
- Threshold semantics: implicit all cases should pass; no explicit gates
- Baseline support: legacy keyword classifier metrics
- Split support: none
- Output format: ad hoc dictionary
- Reproducibility: deterministic taxonomy workflow, no model calls
- Failure behavior: malformed cases raise Python exceptions
- CI compatibility: pytest wrapper exists; no unified CLI
- Known limitations: no true held-out split; multi-label precision is intentionally modest; tiny calibration set

### Pattern Transfer

- Runner: `backend/app/evaluation/pattern_transfer_eval.py::evaluate_pattern_transfer_cases`
- Cases: `evals/pattern_transfer/cases.jsonl`
- Capability: Pattern Transfer Skill/workflow
- Dataset format: JSONL
- Case schema: case id, split, source problem, learner state, memory, expected transfer type, expected target or forbidden target, structure marker
- Metrics: recommendation relevance, transfer-type accuracy, structural-bridge correctness, same-topic shortcut rate, unsupported-claim rate, provenance completeness, structured-output validity; split metrics for development, held-out, adversarial
- Pass/fail semantics: expected transfer type and target behavior satisfied, bridge contains required structure, unsupported/provenance/structure checks pass
- Threshold semantics: implicit all cases should pass; no explicit gates
- Baseline support: same-topic relevance approximation
- Split support: development, heldout, adversarial
- Output format: ad hoc dictionary
- Reproducibility: deterministic transfer corpus and policy, no model calls
- Failure behavior: malformed cases raise Python exceptions
- CI compatibility: pytest wrapper exists; no unified CLI
- Known limitations: heldout/adversarial cases were visible during development; corpus is small and curated

## Fragmentation Found

- Case schemas differ substantially and lack a common envelope.
- Result schemas use inconsistent names: `workflow_precision`, `new_metrics`, `development_metrics`, `provenance_completeness`, `provenance_completeness_rate`.
- Split handling exists only for Pattern Transfer.
- Baseline comparison exists for Code Review, Problem Intelligence, and Pattern Transfer, but not Hinting.
- Thresholds are implicit in pytest assertions; no gate policy separates measurement from release gating.
- Failure categories are booleans rather than typed failure taxonomy entries.
- Error handling is inconsistent; malformed cases usually raise raw exceptions.
- Output formatting is ad hoc; no shared human-readable or machine-readable artifact format exists.
- Metric definitions are embedded inside capability-specific scripts.
- No run id, eval version, implementation version, duration, or artifact path is captured uniformly.
- No CLI can run all suites or filter by split.
- No accepted-baseline artifact exists for regression-aware gating.

## Eval Leakage Risks

- Current deterministic rules were tuned while cases were visible in the same development thread, especially for recent classification and transfer phases.
- Pattern Transfer has `heldout` and `adversarial` labels, but those cases were used during tuning and should be treated as named splits, not true blind holdouts.
- Curated metadata and static transfer edges overlap with eval labels in some cases. This is acceptable for a small deterministic regression suite but not evidence of broad generalization.
- No evidence was found of case IDs being hardcoded into implementation logic.
- No checked-in eval cases appear to contain secrets, credentials, or private learner data.

## Architecture Hypothesis Validation

Validated with adaptation:

```text
Unified Evaluation Platform
  = Common Eval Case Protocol
  + Capability-Specific Adapters
  + Common Runner
  + Metric Registry
  + Result Schema
  + Threshold / Gate Policy
  + Baseline Comparison
  + Split Support
  + Artifact Reporting
  + Regression Support
```

The platform should wrap existing deterministic runners first, not replace them. Old runners remain parity references until unified output is trusted.
