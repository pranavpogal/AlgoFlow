# ADK Runtime Integration Specification

Status: Narrow Tool-Orchestrated Runtime Slice Implemented
Owner: AlgoFlow
Phase: Real Tool-Orchestrated Agent Workflows

## Purpose

Define how Google ADK enters the real request path without creating decorative multi-agent behavior.

## Current Scope

Implemented narrow runtime slice:

- New route: `POST /api/v1/mentor/route`.
- Runtime: `AdkCoordinatorRuntime`.
- Real ADK object: a narrow `google.adk.agents.Agent` coordinator with structured output schema.
- Current routed capabilities: `problem_analysis`, `next_hint`, `recommendations`, and `pattern_transfer`.
- Deterministic fallback: always available and used when `ENABLE_LIVE_ADK=false`.
- Live invocation: available only when `ENABLE_LIVE_ADK=true` and `GOOGLE_API_KEY` is configured.
- Tool request contract: `CoordinatorDecision.tool_requests` can request only `problem.detect_pattern` or `problem.related_problems`.
- Tool execution boundary: every requested tool is rebuilt from trusted server context and executed only through `ToolGateway`.
- Trajectory capture: request ID, trace ID, session ID, runtime mode, selected capability, selected Skill, fallback status, timing, and events.
- Trajectory persistence: `agent_trajectories` stores the route trajectory after execution.

## Non-Goals

- Invoking every existing agent.
- Connecting the old all-subagent root coordinator.
- Replacing deterministic workflows.
- Calling live Gemini in CI.
- Adding memory retrieval, BKT, secure execution, cloud deployment, or broad refactoring.

## Current Runtime Path

```text
POST /api/v1/mentor/route
  -> request/trace middleware
  -> MentorService.route_mentor_request
  -> AdkCoordinatorRuntime.route
  -> real ADK Agent boundary built
  -> live invocation only when explicitly enabled and credentialed
  -> deterministic fallback decision on disabled config, missing key, timeout, invalid output, or failure
  -> ADK tool request capture when present
  -> ToolGateway structural + semantic policy enforcement
  -> existing deterministic workflow
  -> persist trajectory
  -> response + trajectory
```

## Agent Boundary Rules

Use ADK only when autonomous routing or trajectory capture provides value. Current implementation uses one narrow coordinator and no sub-agents.

Do not use ADK when deterministic logic or a bounded Skill is sufficient.

## Runtime Limits

Current slice:

- Coordinator ADK Agent timeout: 3 seconds.
- Direct ADK Agent tools: none.
- ADK tool request IDs: `problem.detect_pattern`, `problem.related_problems`.
- Gateway-mediated runtime tool execution: requested tools execute only through `ToolGateway` after structural and semantic policy checks.
- Trusted arguments: `problem.detect_pattern` title/description are rebuilt from the server request; `problem.related_problems` pattern is derived from trusted detected pattern when available or from the bounded request argument for explicit recommendation mode.
- Sub-agents: none.
- Output schema: `CoordinatorDecision`.
- Fallback: deterministic route selection.
- Live invocation: enabled only when `ENABLE_LIVE_ADK=true` and `GOOGLE_API_KEY` exists.
- Live invoker: `LiveAdkDecisionInvoker` using ADK `Runner` and `InMemorySessionService`.
- Live event cap: `LIVE_ADK_MAX_EVENTS`.

## Trajectory Schema

Schema version: `trajectory-v1`.

Fields:

```json
{
  "schema_version": "trajectory-v1",
  "trajectory_id": "traj_...",
  "request_id": "req_...",
  "trace_id": "trace_...",
  "session_id": "session_...",
  "task": "mentor_route",
  "runtime_mode": "adk_disabled",
  "selected_capability": "problem_analysis",
  "fallback_used": true,
  "started_at": "...",
  "finished_at": "...",
  "duration_ms": 0,
  "events": []
}
```

Events include ADK agent construction, invocation skipped/started/completed/failed, live runner events, route selection, ADK tool request capture, structural policy evaluation, semantic policy evaluation, tool completion/denial, deterministic fallback, workflow execution, and response validation.

## Trajectory Storage

Stored in `agent_trajectories` with:

- trajectory ID
- user ID
- request ID
- trace ID
- session ID
- task
- runtime mode
- selected capability
- selected Skill
- fallback flag
- duration
- event count
- full event JSON

Read endpoint:

```text
GET /api/v1/agent-trajectories/{trajectory_id}
```

Reads are scoped to the resolved principal.

## Tool Gateway Integration

The narrow route consumes `CoordinatorDecision.tool_requests`. The ADK Agent itself still
receives no direct executable tools. Tool requests are recorded as `ADK_TOOL_REQUESTED`,
then executed only through `ToolGateway.call(...)` with caller `adk_narrow_coordinator`.
Tool calls are structurally and semantically policy-gated and recorded as
`TOOL_CALL_COMPLETED` or `TOOL_CALL_DENIED` trajectory events.

If live or mocked ADK returns no tool requests, the route preserves the previous deterministic
default by requesting `problem.detect_pattern` for `problem_analysis` and `next_hint`. If ADK
requests `problem.related_problems` while the selected capability is `next_hint`, semantic
policy denies it as a capability mismatch and no fallback path executes that denied tool.

For `recommendations`, the route executes `problem.related_problems` only when it is explicitly
requested and semantic policy confirms `RECOMMENDATION` intent with `RECOMMEND_TRANSFER` mode.
If no approved recommendation tool request exists, the route returns a safe empty recommendation
response instead of calling the legacy raw recommendation path.

For `pattern_transfer`, the route also requires an explicit approved `problem.related_problems`
request, but uses `RECOMMEND_TRANSFER` intent and `RECOMMEND_TRANSFER` mode. If no approved
pattern-transfer tool request exists, the route returns a safe empty `PatternTransferResponse`
instead of calling the legacy raw pattern-transfer path.

## Evaluation

Explicit suite:

```bash
cd backend
.venv/bin/python -m app.evaluation.cli run --suite adk_routing
.venv/bin/python -m app.evaluation.cli run --suite adk_live_runtime
.venv/bin/python -m app.evaluation.cli run --suite adk_tool_orchestration
```

These suites are not included in `--suite all` yet, preserving the accepted deterministic baseline.

## Rollback

Set `ENABLE_LIVE_ADK=false` or use the existing direct deterministic endpoints. The new route always preserves deterministic fallback.

## Deferred

- Direct ADK tool invocation.
- Trajectory retention/deletion policy.
- ADK routing for additional capabilities beyond pattern transfer.
- Model/token/cost metrics.
- Accepted-baseline promotion for ADK routing suite.
