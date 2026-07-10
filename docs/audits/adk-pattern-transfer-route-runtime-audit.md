# ADK Pattern Transfer Route Runtime Audit

Status: Current
Owner: AlgoFlow
Phase: 23 - Governed Pattern Transfer Capability Routing

## Audit Purpose

Audit the next ADK expansion after governed recommendation routing. The goal is to add one pattern-transfer runtime slice without broadening ADK autonomy, direct tool execution, or legacy compatibility paths.

## Pre-Phase State

The governed `/mentor/route` supported:

- `problem_analysis`
- `next_hint`
- `recommendations`

The semantic policy already allowed `problem.related_problems` for `pattern_transfer`, but `/mentor/route` could not select `pattern_transfer` or serialize a governed `PatternTransferResponse`.

## Implemented Phase 23 Slice

`/mentor/route` now accepts and can select:

- `pattern_transfer`

Runtime behavior:

```text
POST /api/v1/mentor/route
  -> AdkCoordinatorRuntime.route
  -> selected_capability = pattern_transfer
  -> optional tool_requests = problem.related_problems
  -> ADK_TOOL_REQUESTED
  -> ToolGateway structural policy
  -> semantic policy with RECOMMEND_TRANSFER + RECOMMEND_TRANSFER
  -> PatternTransferResponse
```

## Safety Boundary

The route does not add direct ADK tools. `Agent(..., tools=[], sub_agents=[])` remains unchanged.

Pattern transfer executes `problem.related_problems` only when a bounded ADK decision explicitly requests that tool and `ToolGateway` allows it. The service rebuilds the executable tool payload from trusted route context plus the bounded pattern argument.

If no approved tool request exists, `/mentor/route` returns a safe empty `PatternTransferResponse` with `fallback_reason = policy_gated_tool_unavailable`. It does not call the legacy `/pattern-transfer` Skill as a hidden fallback.

## Existing Compatibility Paths

The legacy `/pattern-transfer` endpoint remains unchanged and still uses the deterministic Pattern Transfer Skill directly. Phase 23 only governs the ADK `/mentor/route` slice.

## Non-Changes

- No new sub-agent graph.
- No direct ADK tool execution.
- No Gemini calls in CI.
- No memory, BKT, secure execution, cloud, or UI expansion.
- No accepted deterministic baseline change.
