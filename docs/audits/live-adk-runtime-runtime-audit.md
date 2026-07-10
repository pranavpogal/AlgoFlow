# Live ADK Runtime Audit

Status: Complete
Owner: AlgoFlow
Phase: 20 - Narrow Live ADK/Gemini Runtime

## Current State Before This Phase

The runtime built a real Google ADK `Agent`, but live invocation only occurred when an explicit invoker was supplied. With `ENABLE_LIVE_ADK=false`, routing used deterministic fallback. With `ENABLE_LIVE_ADK=true` and no invoker, runtime also fell back.

## Architecture Decision

Add one bounded default live ADK invoker for the existing narrow coordinator route only. Do not add tools to the ADK agent. Do not connect decorative sub-agents. Do not broaden routed capabilities beyond `problem_analysis` and `next_hint`.

## Runtime Path

```text
POST /api/v1/mentor/route
  -> request/trace middleware
  -> MentorService.route_mentor_request
  -> AdkCoordinatorRuntime.route
  -> live ADK Runner only if ENABLE_LIVE_ADK=true and GOOGLE_API_KEY exists
  -> CoordinatorDecision schema validation
  -> deterministic fallback on missing config, timeout, invalid output, or invocation failure
  -> ToolGateway problem.detect_pattern with semantic policy
  -> deterministic workflow execution
  -> trajectory + policy persistence
```

## Live Invoker

`LiveAdkDecisionInvoker` uses:

- `google.adk.runners.Runner`
- `google.adk.sessions.InMemorySessionService`
- `google.genai.types.Content` / `Part`
- existing `CoordinatorDecision` Pydantic schema validation

The ADK agent still has:

- no direct tools
- no sub-agents
- no code execution
- timeout control through `LIVE_ADK_TIMEOUT_SECONDS`
- event cap through `LIVE_ADK_MAX_EVENTS`

## Fallback Behavior

Fallback occurs when:

- `ENABLE_LIVE_ADK=false`
- `ENABLE_LIVE_ADK=true` but `GOOGLE_API_KEY` is missing
- ADK dependencies are unavailable
- ADK invocation times out
- ADK response does not validate against `CoordinatorDecision`
- invoker raises any exception

## Trajectory Evidence

Phase 20 adds `ADK_LIVE_EVENT_RECEIVED` for bounded live runner events. Existing events remain:

- `ADK_INVOCATION_STARTED`
- `ADK_INVOCATION_COMPLETED`
- `ADK_INVOCATION_FAILED`
- `ADK_INVOCATION_SKIPPED`
- `DETERMINISTIC_FALLBACK_USED`
- `ROUTE_SELECTED`

## Policy Boundary

Live ADK produces only the routing decision. It does not execute tools. Tool execution still happens after routing through `ToolGateway`, structural policy, semantic policy, trajectory capture, and persistent policy records.

## Verification Strategy

CI does not call Gemini. The new `adk_live_runtime` eval suite uses bounded mock invokers and no-key fallback cases to verify the live boundary, fallback behavior, trajectory events, and deterministic parity.

## Known Limitations

- No CI call to real Gemini.
- No live ADK tool invocation.
- No token/cost accounting yet.
- In-memory ADK sessions only for this narrow route.
- No retry beyond deterministic fallback.
