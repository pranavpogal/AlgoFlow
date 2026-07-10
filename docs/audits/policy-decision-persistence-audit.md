# Policy Decision Persistence Audit

Status: Complete
Owner: AlgoFlow
Phase: Policy Decision Persistence Before Live ADK Tool Use

## Current State Before This Phase

Phase 17 introduced a local structural `ToolGateway` and trajectory events for gateway-mediated tool calls. Policy decisions were visible inside `TOOL_CALL_COMPLETED` and `TOOL_CALL_DENIED` trajectory events, but they were not stored as standalone audit records.

## Architecture Decision

Persist policy decisions only for the narrow `/mentor/route` runtime path that already uses the gateway. Do not broaden tool authority, connect decorative agents, enable live Gemini calls, or route additional service paths through the gateway in this phase.

## Persistent Record Added

`backend/app/db/base.py` now defines `PolicyDecisionRecord` using the `policy_decisions` table.

Stored fields include:

- request identity: `request_id`, `trace_id`, `session_id`, `trajectory_id`
- ownership: `user_id`
- tool boundary: `tool_id`, `caller`, `operation`, `risk`
- policy outcome: `decision`, `policy_id`, `reason`
- execution outcome: `success`, `error`, `latency_ms`
- scoped metadata: `decision_metadata`

## Runtime Path

```text
POST /api/v1/mentor/route
  -> AdkCoordinatorRuntime deterministic route decision
  -> ToolGateway.call(problem.detect_pattern)
  -> policy decision captured in ToolCallRecord
  -> trajectory stores TOOL_CALL_COMPLETED
  -> agent_trajectories row persisted
  -> policy_decisions row persisted with matching request/trace/session/trajectory identity
```

## Read Path

`GET /api/v1/agent-trajectories/{trajectory_id}/policy-decisions` returns policy decisions scoped to the resolved principal and trajectory ID.

This intentionally avoids adding a broad policy-log browser before production auth and admin authorization exist.

## Preserved Behavior

- Live ADK/Gemini invocation remains disabled by default.
- Existing deterministic workflows and accepted baseline are preserved.
- Legacy direct service paths are not migrated in this phase.
- Tool calls remain local and low risk.

## Known Limitations

- No migration framework; local startup still creates tables through SQLAlchemy metadata.
- Only the narrow `/mentor/route` gateway call persists standalone policy decisions.
- Denied gateway calls outside a service persistence context are still trajectory-only unless explicitly persisted by the caller.
- No semantic policy, prompt-injection classifier, or human approval path yet.
- No retention, search, export, or admin review interface for policy decisions.
- No live ADK/Gemini tool execution yet.
