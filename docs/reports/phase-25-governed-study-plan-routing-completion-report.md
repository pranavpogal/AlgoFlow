# Phase 25 Completion Report: Governed Study Plan Capability Routing

Status: Complete
Owner: AlgoFlow
Date: 2026-07-10

## Objective

Extend the narrow ADK route from problem analysis, hinting, recommendations, pattern transfer, and code review to one additional governed capability: study planning. Preserve deterministic planning behavior, trajectory capture, existing direct endpoint compatibility, and accepted-baseline stability.

## Architecture Changes

- Extended `CoordinatorCapability` to include `study_plan`.
- Extended `MentorRouteRequest.requested_capability` to accept `study_plan`.
- Added route-level optional planner inputs: `target_company`, `days_remaining`, and `hours_per_week`.
- Updated deterministic routing to select `study_planning_workflow` for explicit study-plan requests or planner-oriented messages.
- Routed governed `study_plan` requests through `MentorService.study_plan`.
- Preserved direct `/study-plan` compatibility behavior.
- Added route tests and ADK routing eval coverage.

## Runtime Paths

Governed study-plan route:

```text
POST /api/v1/mentor/route
  -> AdkCoordinatorRuntime.route
  -> selected_capability: study_plan
  -> selected_skill: study_planning_workflow
  -> MentorService.study_plan
  -> user_memory_snapshot
  -> derive_learner_state
  -> build_weekly_plan
  -> StudyPlanResponse
  -> StudyPlanGenerated learning event
  -> WORKFLOW_EXECUTED
  -> RESPONSE_VALIDATED
  -> persist trajectory
```

No-tool boundary:

```text
selected_capability: study_plan
  -> no ADK_TOOL_REQUESTED
  -> no ToolGateway call
  -> no policy-decision record required
```

## Trajectory Schema

No schema version change was required. Study-plan route execution uses the existing `trajectory-v1` payload with route selection, workflow execution, response validation, and persisted route metadata.

Representative events:

- `REQUEST_RECEIVED`
- `ADK_AGENT_BUILT`
- `ADK_INVOCATION_SKIPPED` when live ADK is disabled
- `DETERMINISTIC_FALLBACK_USED`
- `ROUTE_SELECTED`
- `WORKFLOW_EXECUTED`
- `RESPONSE_VALIDATED`

## Evaluation Changes

`adk_routing` now includes:

- `route_study_plan_requested_capability`

API tests now include:

- deterministic runtime selection for `study_plan`
- `/mentor/route` study-plan execution without tool-request or tool-completion events

## Verification Results

Focused tests:

```text
cd backend && .venv/bin/pytest -q tests/test_adk_tool_orchestration.py tests/test_evaluation_platform.py
21 passed, 4 warnings
```

Lint:

```text
cd backend && .venv/bin/ruff check app tests
All checks passed
```

Explicit routing evaluation:

```text
adk_routing: 7 passed / 7
routing_accuracy: 1.0
trajectory_event_coverage: 1.0
trajectory_identity_completeness: 1.0
fallback_policy_accuracy: 1.0
```

Full verification was run after documentation updates and is summarized in the final phase handoff.

Full backend tests:

```text
cd backend && .venv/bin/pytest -q
97 passed, 5 warnings
```

Additional explicit evaluations:

```text
adk_tool_orchestration: 9 passed / 9
semantic_tool_policy: 19 passed / 19
suite all: 66 passed / 66
```

Accepted deterministic baseline:

```text
status: pass
current_run_id: eval_20260710T081715Z_c2025e4e
caseset_drift: false for code_review, hinting, pattern_transfer, problem_intelligence
blocking_regressions: []
warnings: []
```

Frontend build:

```text
cd frontend && node node_modules/next/dist/bin/next build
Compiled successfully
Generated 12 static pages
```

## Baseline Impact

No accepted deterministic baseline fixture was changed. The new study-plan case is part of the explicit `adk_routing` suite and not part of accepted `--suite all`.

## Fallbacks

- `ENABLE_LIVE_ADK=false` still uses deterministic route selection.
- Study planning does not require a tool fallback because it is a deterministic workflow with scoped service-layer memory access.
- Direct `/study-plan` remains available as the deterministic compatibility endpoint.

## Known Limitations

- The planner still uses the existing deterministic weekly-plan builder.
- Planner quality remains bounded by current memory snapshot and learner-state derivation quality.
- No RAG retrieval, BKT update, calendar integration, adaptive rescheduling loop, or broad planner agent was added.
- CI uses deterministic and mocked ADK paths; no live Gemini planner quality is evaluated in this phase.
