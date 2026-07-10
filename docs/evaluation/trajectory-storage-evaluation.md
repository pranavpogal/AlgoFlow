# Trajectory Storage Evaluation

Status: Current
Owner: AlgoFlow

## Purpose

Verify that ADK routing trajectories have stable identity and can be persisted without weakening the deterministic baseline.

## Current Coverage

Tests verify:

- `POST /api/v1/mentor/route` returns `trajectory_id`, `request_id`, `trace_id`, selected capability, selected Skill, runtime mode, and events.
- `GET /api/v1/agent-trajectories/{trajectory_id}` retrieves the stored trajectory for the same resolved user.
- Stored trajectory event count matches the returned trajectory events.

The explicit `adk_routing` eval verifies:

- `routing_accuracy`
- `trajectory_event_coverage`
- `trajectory_identity_completeness`
- `fallback_policy_accuracy`

## Baseline Relationship

The accepted deterministic baseline remains unchanged. `adk_routing` is still explicit and not included in `--suite all`.

## Current Result

`adk_routing`: 3 cases, 3 passed, all gates passing.
