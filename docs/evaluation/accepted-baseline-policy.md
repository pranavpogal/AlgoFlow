# Accepted Baseline Policy

Status: Current
Owner: AlgoFlow

## Purpose

An accepted baseline is the reviewed behavioral quality snapshot that future deterministic eval runs compare against. It prevents silent regression and gives future ADK/Gemini changes a concrete reference point.

## Storage

Accepted baseline snapshots are checked into the repository:

```text
evals/baselines/accepted/current.json
```

This is the simplest current mechanism because it is reviewable, reproducible, and does not require cloud artifact storage.

## Current Baseline

Baseline ID:

```text
accepted-2026-07-06-deterministic-v1
```

Source revision is `null` because this workspace currently has Git initialized but no `HEAD` commit. Future baselines should capture a real commit SHA once commits exist.

## What The Baseline Contains

- Baseline schema version.
- CI contract version.
- Baseline ID.
- Creation timestamp.
- Source revision where available.
- Suite case counts.
- Case IDs.
- Split counts.
- Suite metrics.
- Built-in legacy/baseline metrics where suites expose them.
- Metric definition versions.
- Metric definition fingerprints.
- Taxonomy versions.
- Human notes.

## Mutation Protection

Normal commands do not mutate the accepted baseline:

```bash
python -m app.evaluation.cli run --suite all
python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json
```

Candidate generation is explicit and requires an output path:

```bash
python -m app.evaluation.cli baseline candidate \
  --output ../evals/baselines/candidates/<candidate>.json \
  --notes "Reason for proposed baseline update"
```

Promotion requires a reviewed commit that intentionally changes `evals/baselines/accepted/current.json`.

## Promotion Requirements

Before promoting a baseline:

- Full backend tests pass.
- Backend lint passes.
- Frontend build passes.
- Unified eval execution succeeds.
- Current comparison result is understood.
- Case count changes are reviewed.
- Metric regressions are explained.
- Metric definition changes are documented.
- The update reason is included in notes or PR description.

## Not Comparable

If metric definition versions or fingerprints differ, comparison reports `not_comparable` instead of pretending old and new metrics are equivalent.

## Security

Untrusted PR code must not silently redefine accepted quality. The CI workflow uses read-only repository permissions and does not run any baseline promotion command.
