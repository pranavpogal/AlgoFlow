# Phase 22 Completion Report: Governed Recommendation Capability Routing

Status: Complete
Owner: AlgoFlow
Date: 2026-07-10

## Objective

Extend the narrow ADK route from problem analysis and hinting to one additional governed capability: recommendations. Preserve deterministic fallbacks, semantic policy, trajectory capture, and accepted-baseline stability.

## Architecture Changes

- Extended `CoordinatorCapability` to include `recommendations`.
- Extended `MentorRouteRequest.requested_capability` to accept `recommendations`.
- Updated deterministic routing to select `pattern_recommendation_workflow` for explicit recommendation requests or recommendation-like messages.
- Added recommendation-mode semantic context in `/mentor/route`:
  - `user_intent = RECOMMENDATION`
  - `mentoring_mode = RECOMMEND_TRANSFER`
- Added governed recommendation response assembly from `problem.related_problems` tool output.
- Added safe recommendation fallback when no approved tool request exists.
- Extended routing and tool-orchestration evaluations for the new capability.

## Runtime Paths

Allowed governed recommendation path:

```text
ADK coordinator decision
  -> selected_capability: recommendations
  -> tool_requests: problem.related_problems
  -> ADK_TOOL_REQUESTED
  -> structural allow
  -> semantic allow INTENT_ALIGNED
  -> TOOL_CALL_COMPLETED
  -> RecommendationResponse
```

No-tool fallback path:

```text
ENABLE_LIVE_ADK=false or no tool request
  -> selected_capability: recommendations
  -> no related-problems tool execution
  -> safe RecommendationResponse with empty related_problems
```

Denied drift path remains:

```text
selected_capability: next_hint
  -> tool_requests: problem.related_problems
  -> semantic deny CAPABILITY_TOOL_MISMATCH
  -> TOOL_CALL_DENIED
  -> safe non-spoiling fallback
```

## Evaluation Changes

`adk_routing` now includes recommendation route selection:

- `route_recommendations_requested_capability`

`adk_tool_orchestration` now includes:

- `adk_related_allowed_for_recommendations`
- `adk_recommendations_disabled_no_tool_bypass`

## Verification Results

Full backend tests:

```text
cd backend && .venv/bin/pytest -q
87 passed, 5 warnings
```

Focused tests:

```text
cd backend && .venv/bin/pytest -q tests/test_adk_tool_orchestration.py tests/test_adk_runtime_trajectory.py tests/test_semantic_tool_policy.py tests/test_tool_gateway.py
29 passed, 4 warnings
```

Focused route/runtime tests:

```text
cd backend && .venv/bin/pytest -q tests/test_adk_tool_orchestration.py tests/test_adk_runtime_trajectory.py
12 passed, 4 warnings
```

Lint:

```text
cd backend && .venv/bin/ruff check app tests
All checks passed
```

Explicit evaluations:

```text
adk_routing: 4 passed / 4
adk_tool_orchestration: 5 passed / 5
adk_live_runtime: 4 passed / 4
semantic_tool_policy: 18 passed / 18
```

Accepted deterministic baseline:

```text
cd backend && .venv/bin/python -m app.evaluation.cli compare --baseline ../evals/baselines/accepted/current.json --machine
status: pass
exit_code: 0
caseset_drift: false for code_review, hinting, pattern_transfer, problem_intelligence
blocking_regressions: []
```

Frontend build:

```text
cd frontend && node node_modules/next/dist/bin/next build
Compiled successfully
Generated 12 static pages
```

## Baseline Impact

No accepted deterministic baseline suite was changed. The new routing and orchestration cases are explicit ADK/policy suites, not part of `--suite all`.

## Known Limitations

- Recommendation routing requires an approved `problem.related_problems` request; no pattern-detection prerequisite tool is added in recommendation mode yet.
- Legacy `/recommendations` remains a compatibility path outside the governed ADK route.
- CI uses mocked ADK decisions for tool-orchestration behavior and does not call Gemini.
- No user acceptance/rejection loop or recommendation memory update was added.
