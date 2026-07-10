# ADK Tool Orchestration Runtime Audit

Status: Current
Owner: AlgoFlow
Phase: 21 - Real Tool-Orchestrated Agent Workflows

## Audit Purpose

Audit the existing ADK/runtime/tool path before adding live tool orchestration. The phase constraint is narrow: allow the coordinator to request selected tools, but keep execution deterministic, policy-gated, traceable, and reversible.

## Pre-Phase Runtime Path

```text
POST /api/v1/mentor/route
  -> MentorService.route_mentor_request
  -> AdkCoordinatorRuntime.route
  -> CoordinatorDecision for problem_analysis or next_hint
  -> server-side ToolGateway.call(problem.detect_pattern)
  -> deterministic workflow response
  -> trajectory + policy-decision persistence
```

The ADK coordinator did not express tool requests. The service always inserted `problem.detect_pattern` for the two narrow routed capabilities.

## Implemented Runtime Path

```text
POST /api/v1/mentor/route
  -> request/trace/session identity
  -> AdkCoordinatorRuntime.route
  -> CoordinatorDecision.tool_requests
  -> ADK_TOOL_REQUESTED trajectory event
  -> trusted server argument reconstruction
  -> ToolGateway structural policy
  -> semantic mentoring policy
  -> deterministic tool handler or denial
  -> selected deterministic workflow
  -> trajectory + policy-decision persistence
```

## Allowed Tool Request Surface

- `problem.detect_pattern`
- `problem.related_problems`

No ADK direct tools are registered. `google.adk.agents.Agent(..., tools=[], sub_agents=[])` remains the runtime boundary.

## Trusted Argument Policy

The coordinator may provide `arguments` for observability, but executable arguments are rebuilt by the server:

- `problem.detect_pattern`: uses route `title` and `description`.
- `problem.related_problems`: uses already detected pattern when available, otherwise a bounded string pattern argument.

This prevents model-provided arguments from silently redefining the trusted task.

## Fallback Behavior

If the coordinator returns no tool requests, `/mentor/route` preserves the prior behavior by creating a default `problem.detect_pattern` request for `problem_analysis` and `next_hint`.

If a requested tool is denied, the route records the denial and uses the safe non-tool fallback. It does not call raw tools after denial.

## Trajectory Events

Phase 21 adds:

- `ADK_TOOL_REQUESTED`

Existing gateway events remain:

- `STRUCTURAL_POLICY_EVALUATED`
- `SEMANTIC_POLICY_EVALUATED`
- `TOOL_CALL_COMPLETED`
- `TOOL_CALL_DENIED`

## Non-Changes

- No new broad agent graph.
- No direct ADK tool execution.
- No Gemini/live CI calls.
- No memory, BKT, secure execution, cloud, or unrelated refactor.
- No accepted baseline caseset change.
