# Tool Gateway Evaluation

Status: Current
Owner: AlgoFlow

## Purpose

Verify that tool calls used by the ADK routing slice are typed, policy-gated, and visible in trajectory data.

## Current Test Coverage

`backend/tests/test_tool_gateway.py` verifies:

- allowed read tool execution
- caller denial
- invalid input rejection
- draft related-problem tool metadata
- trajectory event recording for completion and denial
- persistent policy-decision storage with request, trace, session, and trajectory identity

## Current Eval Coverage

`adk_routing` cases require `TOOL_CALL_COMPLETED` in the trajectory event list.
`backend/tests/test_adk_runtime_trajectory.py` also verifies that `/mentor/route`
persists an allow decision for `problem.detect_pattern` and that the decision is
retrievable through the trajectory-scoped policy-decision endpoint.

Run:

```bash
cd backend
.venv/bin/python -m app.evaluation.cli run --suite adk_routing
```

## Baseline Relationship

The accepted deterministic baseline remains unchanged. Tool-gateway eval coverage is explicit through `adk_routing` and CI, but not included in `--suite all`.
