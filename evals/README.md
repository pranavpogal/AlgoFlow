# AlgoFlow Evaluation Suites

AlgoFlow uses deterministic evaluation suites to measure mentoring behavior beyond ordinary unit tests. The unified platform lives under `backend/app/evaluation/` and adapts current suite-specific evaluators into one common runner.

## Current Suites

- `hint_leakage/`: progressive hint intervention correctness and solution-leakage checks.
- `code_review/`: senior-engineer review behavior, workflow precision, legacy precision, unsupported claims, rewrite policy, and structured output.
- `problem_classification/`: primary topic, pattern precision/recall, multi-label behavior, provenance, unsupported claims, and baseline comparison.
- `pattern_transfer/`: recommendation relevance, transfer type, structural bridge correctness, same-topic shortcut detection, provenance, and development/held-out/adversarial split metrics.

## Commands

Run from `backend/`:

```bash
.venv/bin/python -m app.evaluation.cli list
.venv/bin/python -m app.evaluation.cli metrics
.venv/bin/python -m app.evaluation.cli run --suite all
.venv/bin/python -m app.evaluation.cli run --suite pattern_transfer --split adversarial
.venv/bin/python -m app.evaluation.cli run --suite all --json
```

## Artifacts

`--json` writes machine-readable artifacts to `evals/artifacts/<run_id>/`:

- `summary.json`
- `cases.json`
- `failures.json`
- `baseline_comparison.json` for accepted-baseline comparison runs

Artifacts are ignored by Git.

## Accepted Baseline

The current accepted deterministic baseline is checked in at:

```text
evals/baselines/accepted/current.json
```

Normal eval runs do not mutate this file. Generate proposed replacements explicitly:

```bash
cd backend
.venv/bin/python -m app.evaluation.cli baseline candidate \
  --output ../evals/baselines/candidates/<candidate>.json \
  --notes "Reason for baseline update"
```

## Engineering Rule

Do not claim AI behavior improved without running the relevant evals. Do not modify capability behavior merely to improve scores. If a metric changes, document whether it is a behavioral change, metric-definition change, or fixture change.
