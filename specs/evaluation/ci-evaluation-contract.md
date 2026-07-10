# CI Evaluation Contract Specification

Status: Current
Owner: AlgoFlow
Contract Version: `ci-eval-contract-v1`

## Purpose

The CI evaluation contract makes AlgoFlow's deterministic behavioral evaluations operationally useful for software delivery. It answers whether a change preserves accepted quality, creates behavioral regressions, changes the caseset, or fails because of infrastructure.

## PR Gate Contract

Run on every pull request and push to `main`:

- Backend tests: `pytest -q`
- Backend lint: `ruff check app tests`
- Deterministic eval comparison: `python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json --json`
- Frontend production build: `npm run build`

The current all-suite deterministic eval run is cheap enough for every PR. Local measurement: 66 cases in about `0.035s`; accepted-baseline comparison in about `0.043s`.

## Suites And Splits

PR gate runs all current deterministic suites:

- `hinting`: development split only.
- `code_review`: development split only.
- `problem_intelligence`: development split only.
- `pattern_transfer`: development, heldout, and adversarial fixture splits.

No live Gemini, live ADK runtime, vector-memory retrieval changes, or model-assisted judge is part of the PR gate.

## Absolute Gates

Absolute gates remain in `backend/app/evaluation/core/thresholds.py`. They catch safety and policy failures in the current run.

## Relative Regression Gates

Relative comparison lives in `backend/app/evaluation/core/baseline.py` as `RELATIVE_REGRESSION_POLICIES`.

Blocking relative policies include:

- Suite pass rate must not regress.
- Hinting intervention correctness and solution leakage must not regress.
- Unsupported-claim rates must not increase.
- Code rewrite-policy compliance must not regress.
- Pattern-transfer same-topic shortcut rate must not increase.
- Pattern-transfer provenance completeness must not regress.

Warning policies include small-data quality signals such as workflow precision, primary topic accuracy, pattern precision/recall, recommendation relevance, and transfer type accuracy.

Informational metrics are still reported but not used as blocking relative gates unless explicitly promoted later.

## Exit Codes

- `0`: tests/evals executed and no blocking gate or blocking baseline regression failed.
- `1`: behavioral failure, including absolute gate failure or blocking baseline regression.
- `2`: infrastructure failure, invalid baseline, invalid suite, or case-loading failure.

## Baseline Selection

The default accepted baseline is:

```text
evals/baselines/accepted/current.json
```

Baseline ID:

```text
accepted-2026-07-06-deterministic-v1
```

## Baseline Update Policy

Normal eval and compare commands must not mutate the accepted baseline. Candidate baseline generation is explicit:

```bash
cd backend
python -m app.evaluation.cli baseline candidate \
  --output ../evals/baselines/candidates/<candidate>.json \
  --notes "Reason for proposed update"
```

Promotion happens only by reviewing and committing an intentional change to `evals/baselines/accepted/current.json`.

## Artifact Behavior

`--json` writes local or CI artifacts under `evals/artifacts/<run_id>/`:

- `summary.json`
- `cases.json`
- `failures.json`
- `baseline_comparison.json` for compare runs

CI uploads these artifacts with 14-day retention.

## Timeout Behavior

GitHub Actions jobs use 15-minute job timeouts. The deterministic eval code itself does not currently implement per-case timeouts because current suites are local and deterministic.

## Future ADK/Gemini Readiness

The accepted-baseline model stores suite metrics, metric definition fingerprints, case IDs, split counts, taxonomy versions, and source revision where available. Future ADK/Gemini suites can add metrics for routing, trajectory length, tool calls, fallback rate, latency, token usage, and cost without overwriting the deterministic contract.
