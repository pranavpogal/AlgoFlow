# Local CI Contract Guide

Status: Current
Owner: AlgoFlow

Run these commands before opening or updating a PR.

## Backend

```bash
cd backend
.venv/bin/pytest -q
.venv/bin/ruff check app tests
.venv/bin/python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json
```

## Frontend

```bash
cd frontend
npm run build
```

## Machine-Readable Comparison

```bash
cd backend
.venv/bin/python -m app.evaluation.cli compare \
  --baseline ../evals/baselines/accepted/current.json \
  --machine
```

## Write Artifacts

```bash
cd backend
.venv/bin/python -m app.evaluation.cli compare \
  --baseline ../evals/baselines/accepted/current.json \
  --json
```

Artifacts are written to `evals/artifacts/<run_id>/`.

## Candidate Baseline

Generate a candidate only when intentionally proposing a baseline update:

```bash
cd backend
.venv/bin/python -m app.evaluation.cli baseline candidate \
  --output ../evals/baselines/candidates/<candidate>.json \
  --notes "Why this baseline should be reviewed"
```

A candidate file is not accepted until it is reviewed and promoted through a normal repository change.

## Exit Codes

- `0`: pass.
- `1`: behavioral gate or blocking regression failure.
- `2`: infrastructure, invalid baseline, invalid suite, or case-loading failure.
