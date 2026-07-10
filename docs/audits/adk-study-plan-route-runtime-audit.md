# ADK Study Plan Route Runtime Audit

Status: Current-state audit before Phase 25 implementation
Owner: AlgoFlow
Date: 2026-07-10

## Current Governed Route

The governed `/api/v1/mentor/route` path currently supports:

- `problem_analysis`
- `next_hint`
- `recommendations`
- `pattern_transfer`
- `code_review`

The route captures trajectory data, persists the trajectory, and records policy decisions for gateway-mediated tool calls.

## Current Study Plan Path

The direct deterministic endpoint exists:

```text
POST /api/v1/study-plan
  -> MentorService.study_plan
  -> user_memory_snapshot
  -> derive_learner_state
  -> build_weekly_plan
  -> StudyPlanResponse
  -> StudyPlanGenerated learning event
```

This path is deterministic and does not require a ToolGateway call. It reads scoped relational memory through the service layer and writes a learning event.

## Gap

`/mentor/route` cannot currently select `study_plan`, so the ADK coordinator trajectory does not cover planner routing. This leaves study planning outside the governed routing surface even though it is one of the mentor's core product capabilities.

## Proposed Narrow Slice

Add a no-new-tool governed route capability:

```text
POST /api/v1/mentor/route
  -> AdkCoordinatorRuntime.route
  -> selected_capability: study_plan
  -> selected_skill: study_planning_workflow
  -> MentorService.study_plan
  -> WORKFLOW_EXECUTED
  -> RESPONSE_VALIDATED
  -> persist trajectory
```

## Boundary Rules

- Do not add a planner tool.
- Do not add memory retrieval/RAG.
- Do not add Gemini planner generation.
- Do not change the accepted deterministic baseline.
- Do not call raw fallback after semantic denial because this phase has no tool policy decision path.
- Preserve the direct `/study-plan` compatibility endpoint.

## Expected Evaluation Changes

- Add one `adk_routing` case for `study_plan` route selection.
- Add API tests proving route response shape and no tool execution events.
- Keep `adk_tool_orchestration`, `semantic_tool_policy`, and accepted `--suite all` stable unless explicitly extended later.

## Known Limitations

- The planner still uses the existing deterministic weekly-plan builder.
- Planner quality remains bounded by current learner-state and memory snapshot quality.
- No longitudinal planner agent, calendar integration, or adaptive rescheduling loop is added.
