# Evaluation Authoring Guide

Status: Current
Owner: AlgoFlow

## Principles

Evaluation cases should measure behavior, not implementation details. Do not add cases that merely mirror hardcoded rules, exact prompt snippets, or table lookups unless the purpose is a regression test for a known issue.

## Common Case Envelope

New suites should be adaptable to this envelope:

```json
{
  "case_id": "unique_case_id",
  "suite": "suite_name",
  "capability": "capability_name",
  "split": "development",
  "tags": [],
  "input": {},
  "expected": {},
  "forbidden": {},
  "metadata": {},
  "provenance": {}
}
```

Existing suites may keep their capability-specific JSONL schemas while adapters translate them into the common result protocol.

## Split Semantics

- `development`: visible during feature development.
- `held_out`: intended to reduce overfitting, but do not claim strict holdout status if repeatedly used during tuning.
- `adversarial`: designed to expose known failure modes.
- `regression`: derived from a prior bug or behavior failure.
- `production_replay`: deferred until sanitized replay governance exists.

## Adding A Case

1. Add one JSONL row to the relevant `evals/<suite>/cases.jsonl` file.
2. Prefer clear expected and forbidden behavior over free-form prose.
3. Include split and tags where the suite supports them.
4. Run the legacy evaluator and the unified runner.
5. If behavior changes, document whether the change is expected.

## Adding A Suite

1. Create deterministic case fixtures.
2. Create or reuse a capability-specific evaluator.
3. Add an adapter under `backend/app/evaluation/adapters/`.
4. Register it in `backend/app/evaluation/core/registry.py`.
5. Add metrics to `backend/app/evaluation/core/metrics.py`.
6. Add gates only after measurement semantics are understood.
7. Add platform tests for registration, split handling, artifacts, and exit codes.

## Leakage Rules

Avoid hardcoding case IDs or exact expected labels into production capability logic. If a known problem requires canonical metadata, document the source and use it as product knowledge rather than hidden eval-specific tuning.
