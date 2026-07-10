# Evaluation Platform Specification

Status: Implemented Core Platform
Owner: AlgoFlow
Phase: Unified Evaluation Platform Consolidation

## Purpose

Define how AlgoFlow measures probabilistic and semi-deterministic mentoring intelligence beyond unit tests. The platform must support evidence-based engineering decisions without requiring live Gemini, ADK, or cloud services for deterministic CI runs.

## Current Scope

Current unified suites:

- Progressive hinting.
- Code review.
- Problem intelligence / classification.
- Pattern transfer.

Future suites may include ADK routing, skill triggering, tool selection, memory retrieval, context construction, learner-state quality, mock-interview quality, session convergence, and end-to-end tutoring behavior.

## Non-Goals

- Rewriting working capability logic merely to improve scores.
- Adding live ADK/Gemini calls for appearance.
- Treating evals as replacements for pytest.
- Creating a distributed evaluation service before local deterministic evaluation is stable.

## Common Case Protocol

The common case envelope is represented by `EvalCaseEnvelope` and is intended for new suites:

```json
{
  "case_id": "...",
  "suite": "...",
  "capability": "...",
  "split": "development",
  "tags": [],
  "input": {},
  "expected": {},
  "forbidden": {},
  "metadata": {},
  "provenance": {},
  "raw_case": {}
}
```

Existing suites may keep their current JSONL shape while adapters translate outputs into the common result protocol.

## Common Result Protocol

The executable result model lives in `backend/app/evaluation/core/models.py`:

```json
{
  "case_id": "...",
  "suite": "...",
  "capability": "...",
  "split": "...",
  "status": "passed",
  "metrics": {},
  "checks": [],
  "failures": [],
  "latency_ms": null,
  "token_usage": null,
  "model_calls": null,
  "tool_calls": null,
  "trace_id": null,
  "implementation_version": null,
  "eval_version": "eval-platform-v1",
  "raw_result": {}
}
```

Failure categories include intent mismatch, solution leakage, repetition, unsupported claim, wrong classification, wrong transfer type, invalid structure, missing provenance, policy violation, execution error, timeout, infrastructure failure, invalid case, and metric failure.

## Metric Registry

The metric registry lives in `backend/app/evaluation/core/metrics.py`. Each metric defines ID, name, capability, formula, range, direction, aggregation, missing-data behavior, threshold semantics, and limitations.

## Gate Policy

Gates live in `backend/app/evaluation/core/thresholds.py` and separate measurement from release gating. Current blocking gates are derived from observed passing deterministic behavior, including zero solution leakage, zero unsupported claims, required structured-output/provenance validity, and zero same-topic shortcut rate.

## Runner And CLI

```bash
cd backend
.venv/bin/python -m app.evaluation.cli list
.venv/bin/python -m app.evaluation.cli metrics
.venv/bin/python -m app.evaluation.cli run --suite all
.venv/bin/python -m app.evaluation.cli run --suite pattern_transfer --split adversarial
.venv/bin/python -m app.evaluation.cli run --suite all --json
.venv/bin/python -m app.evaluation.cli run --suite all --machine
```

Exit codes:

- `0`: execution succeeded and no blocking gate failed.
- `1`: execution succeeded but a blocking gate failed.
- `2`: infrastructure or case-loading failure.

## Artifacts

`--json` writes:

- `evals/artifacts/<run_id>/summary.json`
- `evals/artifacts/<run_id>/cases.json`
- `evals/artifacts/<run_id>/failures.json`

Artifacts are runtime outputs and are ignored by Git.

## Baseline Support

Adapters preserve existing baselines:

- Code review keeps legacy precision.
- Problem intelligence keeps baseline topic and pattern metrics.
- Pattern transfer keeps baseline same-topic relevance.

Accepted-current baseline snapshots and trend storage are deferred until CI artifact retention exists.

## Split Support

The runner supports a split filter. Current pattern-transfer cases use `development`, `heldout`, and `adversarial` splits. The standard terminology for future datasets is `development`, `held_out`, `adversarial`, `regression`, and deferred `production_replay`.

## Current Limitations

- No live model or ADK trajectory evaluation is included in this phase.
- Confidence calibration interfaces are prepared only conceptually; current datasets are too small for strong calibration claims.
- Existing case schemas are not force-migrated to one JSON shape.
- Held-out status is limited by repeated local use during development.
