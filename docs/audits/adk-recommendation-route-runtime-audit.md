# ADK Recommendation Route Runtime Audit

Status: Current
Owner: AlgoFlow
Phase: 22 - Governed Recommendation Capability Routing

## Audit Purpose

Audit the next ADK expansion after Phase 21 tool-request orchestration. The goal is to add one additional governed capability without reviving decorative multi-agent architecture or direct ADK tool execution.

## Pre-Phase State

The governed route supported:

- `problem_analysis`
- `next_hint`

The coordinator could request:

- `problem.detect_pattern`
- `problem.related_problems`

However, `problem.related_problems` was only evaluated as a denied request in hint mode. There was no semantically aligned recommendation capability on `/mentor/route`.

## Implemented Phase 22 Slice

`/mentor/route` now accepts and can select:

- `recommendations`

Runtime behavior:

```text
POST /api/v1/mentor/route
  -> AdkCoordinatorRuntime.route
  -> selected_capability = recommendations
  -> optional tool_requests = problem.related_problems
  -> ADK_TOOL_REQUESTED
  -> ToolGateway structural policy
  -> semantic policy with RECOMMENDATION + RECOMMEND_TRANSFER
  -> RecommendationResponse
```

## Safety Boundary

The route does not add direct ADK tools. `Agent(..., tools=[], sub_agents=[])` remains unchanged.

The phase does not broaden `problem.detect_pattern` into recommendation mode. A recommendation route only executes `problem.related_problems` when the coordinator supplies an explicit bounded pattern argument and semantic policy allows the recommendation intent.

If no approved recommendation tool request exists, the route returns a safe `RecommendationResponse` with no raw recommendation fallback.

## Existing Compatibility Paths

The legacy `/recommendations` endpoint remains unchanged and still uses the deterministic pattern-transfer workflow. Phase 22 only governs the ADK `/mentor/route` slice.

## Non-Changes

- No new sub-agent graph.
- No direct ADK tool execution.
- No Gemini calls in CI.
- No memory, BKT, secure execution, cloud, or UI expansion.
- No accepted deterministic baseline change.
