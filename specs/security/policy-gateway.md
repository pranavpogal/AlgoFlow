# Policy Gateway Specification

Status: Structural Tool Gateway with Persistent Policy Decisions
Owner: AlgoFlow
Phase: 1

## Purpose

Define structural and semantic policy enforcement for sensitive actions, tool calls, memory access, and future agent behavior.

## Motivation

Current services read/write memory directly using client-supplied `user_id`. Future ADK/tool execution increases risk unless authorization and intent boundaries are enforced outside model prompts.

## Scope

- Read/draft/act classification.
- Structural gating.
- Semantic gating.
- Tool permission checks.
- Memory access checks.
- Policy decision observability.

## Current Implementation

Phase 17 added an in-process structural tool gateway in `backend/app/core/tool_gateway.py`.
The current gateway registers only low-risk read/draft tools:

- `problem.detect_pattern`
- `problem.related_problems`

It performs caller allowlisting, Pydantic input validation, output type checks, policy
decisions, trajectory event recording, and persistent policy-decision records for the
narrow `/mentor/route` runtime path.

Phase 18 added `policy_decisions` storage in `backend/app/db/base.py`, repository
helpers in `backend/app/memory/repository.py`, and a principal-scoped read endpoint:

- `GET /api/v1/agent-trajectories/{trajectory_id}/policy-decisions`

Phase 19 added deterministic semantic tool policy in `backend/app/core/semantic_policy.py`
and composes it into `ToolGateway` before execution. It still does not provide
external tool access, code execution, async timeout enforcement, or live ADK/Gemini
tool invocation.

## Non-Goals

- Full enterprise IAM design.
- Blocking all local demo workflows.
- LLM-only safety enforcement.

## Capability Classes

- Read: inspect problem, retrieve progress, analyze code, read user memory.
- Draft: propose hint, feedback, study plan, recommendation.
- Act: persist attempt, mutate learner state, store memory, schedule job, execute code.

Act operations require policy evaluation. High-risk act operations may require human approval.

## Structural Gating

Evaluate:

- authenticated user
- tenant/user scope
- environment
- requesting component
- tool/capability identity
- allowed operation
- resource ownership
- risk class

## Semantic Gating

Evaluate:

- current user intent
- requested action relevance
- solution leakage risk
- sensitive data exposure
- prompt-injection indicators
- intent drift

## Policy Decision Schema

```json
{
  "decision": "allow",
  "reason": "user owns requested memory item",
  "policy_id": "memory.read.own_user",
  "risk": "low",
  "request_id": "req_..."
}
```

## Persistent Policy Decision Record

Persisted gateway decisions include:

- `user_id`
- `request_id`
- `trace_id`
- `session_id`
- `trajectory_id`
- `tool_id`
- `caller`
- `operation`
- `risk`
- `decision`
- `policy_id`
- `reason`
- `success`
- `error`
- `latency_ms`
- `decision_metadata`

Phase 19 stores semantic policy details inside `decision_metadata` rather than adding
new database columns. Current metadata includes structural and semantic decision
payloads, semantic policy version, reason code, selected capability, user intent,
mentoring mode, reveal authorization, and injection suspicion when available.

## BDD Scenarios

### Scenario: User Reads Own Analytics

Given authenticated user is `user_a`
When they request `/analytics/user_a`
Then structural policy allows the read

### Scenario: User Reads Another User's Analytics

Given authenticated user is `user_a`
When they request `/analytics/user_b`
Then policy denies the request
And no database query returns user B's data

### Scenario: Hint Request Attempts Code Execution

Given current intent is “give me one hint”
When an agent attempts to call code execution
Then semantic or structural policy denies the tool call

### Scenario: Local Demo Mode

Given environment is local demo
When the request uses `demo-user`
Then policy may allow demo-scoped data access
And the decision is marked as demo-only

## Testing Strategy

- Policy unit tests.
- Route authorization tests.
- Tool denial tests.
- Demo-vs-production config tests.

## Evaluation Strategy

- Intent-drift evals.
- Tool-use trajectory evals.
- Prompt-injection evals.

## Acceptance Criteria

- User-scoped data access cannot depend on client-supplied identity in production.
- Every sensitive tool/memory operation has a policy decision record.
- Denials fail closed with safe error envelopes.
