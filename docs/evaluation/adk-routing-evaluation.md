# ADK Routing And Trajectory Evaluation

Status: Current
Owner: AlgoFlow

## Purpose

Evaluate the first narrow ADK runtime slice without changing the accepted deterministic baseline.

## Suite

```text
evals/adk_routing/cases.jsonl
```

Runner:

```bash
cd backend
.venv/bin/python -m app.evaluation.cli run --suite adk_routing
```

Aliases:

- `routing`
- `trajectory`

## Metrics

- `routing_accuracy`: correct selected capability and Skill.
- `trajectory_event_coverage`: required trajectory events present.
- `trajectory_identity_completeness`: trajectory ID, session ID, and schema version present.
- `fallback_policy_accuracy`: fallback behavior matches expected policy.

## Gates

All four metrics currently require `1.0` because the fixture set is tiny and deterministic.

## Baseline Relationship

The ADK routing suite is not included in `--suite all` yet. This preserves the Phase 14 accepted baseline, which covers the original 66 deterministic cases. Promotion into the accepted baseline should be explicit after the runtime slice matures.

## Current Result

Current local result:

- 7 cases
- 7 passed
- routing accuracy: 1.0
- trajectory event coverage: 1.0
- trajectory identity completeness: 1.0
- fallback policy accuracy: 1.0

The current case set includes explicit routes for hints, problem analysis, recommendations,
pattern transfer, code review, and study planning.
