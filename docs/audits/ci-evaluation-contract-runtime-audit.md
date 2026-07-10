# CI Evaluation Contract Runtime Audit

Status: Complete
Owner: AlgoFlow
Phase: CI Evaluation Contract + Accepted Baseline Snapshot Policy

## Audit Scope

Searched repository for CI/CD and automation behavior, including `.github/workflows`, CI references, workflows, pipelines, pytest, ruff, frontend build commands, evaluation CLI, baseline, artifacts, cache, branch protection, pre-commit, Makefile, shell scripts, Docker, and deployment workflows.

## Existing CI Provider

No existing CI provider configuration was found before this phase. There was no `.github/workflows/` directory and no checked-in workflow file.

## Workflow Files

Before this phase: none.

Related automation files found:

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `docker-compose.yml`
- `scripts/dev.sh`
- `backend/pyproject.toml`
- `frontend/package.json`

## Existing Triggers

None. No CI triggers existed before this phase.

## Existing Jobs

None. No CI jobs existed before this phase.

## Existing Test Commands

Backend tests are configured through `backend/pyproject.toml`:

- `pytest -q`
- pytest test path: `tests`
- pytest python path: `.`

Previously verified local command:

```bash
cd backend
.venv/bin/pytest -q
```

## Existing Lint Commands

Ruff is configured in `backend/pyproject.toml`:

- target version: `py311`
- line length: `100`

Previously verified local command:

```bash
cd backend
.venv/bin/ruff check app tests
```

## Existing Frontend Build Commands

`frontend/package.json` defines:

- `npm run dev`
- `npm run build`
- `npm run start`
- `npm run lint`

The production build command is:

```bash
cd frontend
npm run build
```

## Existing Eval Commands

The previous phase added `backend/app/evaluation/cli.py` with:

```bash
cd backend
.venv/bin/python -m app.evaluation.cli list
.venv/bin/python -m app.evaluation.cli metrics
.venv/bin/python -m app.evaluation.cli run --suite all
.venv/bin/python -m app.evaluation.cli run --suite pattern_transfer --split adversarial
.venv/bin/python -m app.evaluation.cli run --suite all --json
.venv/bin/python -m app.evaluation.cli run --suite all --machine
```

## Unified Evaluation Platform Contract Found

Verified paths:

- `backend/app/evaluation/core/models.py`: common case/result/run protocols and exit-code semantics.
- `backend/app/evaluation/core/runner.py`: common runner and artifact wiring.
- `backend/app/evaluation/core/reporting.py`: human-readable summary and JSON artifact writer.
- `backend/app/evaluation/core/metrics.py`: metric registry.
- `backend/app/evaluation/core/thresholds.py`: absolute gate policy.
- `backend/app/evaluation/core/registry.py`: suite registry.
- `backend/app/evaluation/adapters/`: adapters for hinting, code review, problem intelligence, and pattern transfer.
- `backend/app/evaluation/cli.py`: CLI entry point.

Current verified all-suite eval result:

- Suites: 4
- Cases: 66
- Passed: 66
- Failed: 0
- Exit code: 0

## Artifact Retention

Before this phase: local eval artifacts could be written under `evals/artifacts/<run_id>/`, and `.gitignore` excluded `evals/artifacts/`. No CI artifact retention existed.

## Caching

Before this phase: no CI cache configuration existed.

## Concurrency Behavior

Before this phase: no CI concurrency behavior existed.

## Permissions

Before this phase: no CI permissions existed.

## Secrets Usage

No workflow secret usage existed. The deterministic evaluation contract does not require secrets, Gemini keys, ADK credentials, or deployment credentials.

## Branch Assumptions

No branch protection or CI branch assumptions were found. Git exists, but this workspace has no `HEAD` commit, so accepted baseline provenance records `source_revision: null` honestly.

## Current Failure Semantics

Unified eval CLI semantics before this phase:

- `0`: execution succeeded and no blocking gate failed.
- `1`: blocking behavioral gate failed.
- `2`: evaluation infrastructure/case-loading failure.

This phase preserves that distinction and extends it to accepted-baseline comparison.

## Mismatch With Previous Completion Report

No material mismatch found. The previous phase reported no accepted-baseline retention policy and no historical trend store; both were accurate before this phase.

## Security Findings

- No pre-existing CI workflow could mutate baselines.
- No secrets were required for deterministic validation.
- A future workflow must not let untrusted PR code promote baselines automatically.
- CI should use read-only repository permissions unless a future reviewed need justifies more.
