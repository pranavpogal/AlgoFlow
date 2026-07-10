# Phase 21 Completion Report: Real Tool-Orchestrated Agent Workflows

Status: Complete
Owner: AlgoFlow
Date: 2026-07-10

## Objective

Add the next controlled ADK phase: allow the narrow coordinator to request selected tools while preserving deterministic workflows, semantic policy, fallback behavior, trajectory capture, persistence, and accepted-baseline stability.

## Architecture Changes

- Added `CoordinatorToolRequest` and `CoordinatorDecision.tool_requests`.
- Added `ADK_TOOL_REQUESTED` trajectory event.
- Updated `/mentor/route` to consume ADK tool requests.
- Rebuilt executable tool arguments from trusted server context.
- Preserved `ToolGateway` as the only execution boundary.
- Preserved default `problem.detect_pattern` behavior when ADK returns no tool requests.
- Added explicit `adk_tool_orchestration` evaluation suite and CI gate.

## Runtime Paths

Allowed path:

```text
ADK coordinator decision
  -> tool_requests: problem.detect_pattern
  -> ADK_TOOL_REQUESTED
  -> ToolGateway structural allow
  -> semantic allow
  -> TOOL_CALL_COMPLETED
  -> deterministic workflow response
```

Denied path:

```text
ADK coordinator decision
  -> tool_requests: problem.related_problems during next_hint
  -> ADK_TOOL_REQUESTED
  -> ToolGateway structural allow
  -> semantic deny CAPABILITY_TOOL_MISMATCH
  -> TOOL_CALL_DENIED
  -> safe non-tool fallback
```

Default preserved path:

```text
ENABLE_LIVE_ADK=false
  -> deterministic route decision
  -> default problem.detect_pattern tool request
  -> gateway-mediated completion
```

## Trajectory Schema Change

New event type:

```text
ADK_TOOL_REQUESTED
```

Event metadata includes:

- `tool_id`
- `purpose`
- `provided_argument_keys`
- `trusted_argument_keys`

## Tests And Evaluation Results

Full backend tests:

```text
cd backend && .venv/bin/pytest -q
84 passed, 5 warnings
```

Focused verification:

```text
cd backend && .venv/bin/pytest -q tests/test_adk_tool_orchestration.py tests/test_adk_runtime_trajectory.py tests/test_semantic_tool_policy.py tests/test_tool_gateway.py
26 passed, 4 warnings
```

Lint:

```text
cd backend && .venv/bin/ruff check app tests
All checks passed
```

New explicit suite:

```text
cd backend && .venv/bin/python -m app.evaluation.cli run --suite adk_tool_orchestration --machine
exit_code: 0
case_count: 3
passed: 3
failed: 0
tool_request_execution_accuracy: 1.0
tool_policy_enforcement_accuracy: 1.0
tool_trajectory_coverage: 1.0
tool_fallback_non_bypass_accuracy: 1.0
```

Existing deterministic suite:

```text
cd backend && .venv/bin/python -m app.evaluation.cli run --suite all --machine
exit_code: 0
case_count: 66
passed: 66
failed: 0
```

Accepted baseline comparison:

```text
cd backend && .venv/bin/python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json --machine
status: pass
exit_code: 0
caseset_drift: false for code_review, hinting, pattern_transfer, problem_intelligence
blocking_regressions: []
```

Explicit ADK/policy suites:

```text
adk_routing: 3 passed / 3
adk_live_runtime: 4 passed / 4
semantic_tool_policy: 18 passed / 18
```

Frontend production build:

```text
cd frontend && node node_modules/next/dist/bin/next build
Compiled successfully
Generated 12 static pages
```

## Baseline Comparison

No accepted deterministic baseline cases were changed. `DEFAULT_CI_SUITES` still contains:

- `code_review`
- `hinting`
- `pattern_transfer`
- `problem_intelligence`

The new suite is explicit and blocking in CI, but not part of `--suite all`.

## Regressions

None found in focused tests, Ruff, or the new explicit suite.

## Fallbacks

- Missing/disabled live ADK still uses deterministic routing fallback.
- Missing tool requests still preserve the prior default detect-pattern request.
- Denied tool requests use safe non-tool fallback and do not execute raw tools.

## Known Limitations

- ADK still has no direct executable tools.
- Only two tool request IDs are supported.
- Only `/mentor/route` uses the governed ADK tool-request path.
- Legacy direct endpoints remain as compatibility paths.
- CI uses mocked ADK decisions for this suite and does not call Gemini.
- No token/cost accounting was added in this phase.
