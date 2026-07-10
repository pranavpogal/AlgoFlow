# Semantic Tool Policy Specification

Status: Current
Owner: AlgoFlow
Policy Version: `semantic-tool-policy-v1`

## Purpose

Ensure a structurally authorized tool call is also justified for the current user intent, selected capability, mentoring mode, and task context before execution.

## Architecture Decision

Semantic policy is a deterministic evaluator composed inside `ToolGateway`. It is not an agent, not an LLM judge, and not a generic safety classifier.

```text
ToolGateway
  -> registered tool lookup
  -> structural authorization
  -> input schema validation
  -> semantic policy evaluation
  -> typed execution
  -> output validation
  -> trajectory + persistent policy evidence
```

A semantic allow can never override a structural deny.

## Context Model

`SemanticPolicyContext` contains only fields that can currently be populated honestly:

- trusted identity: `principal_id`, `request_id`, `trace_id`, `session_id`, `trajectory_id`
- trusted runtime selection: `caller_id`, `selected_capability`, `requested_tool_id`, `operation_type`
- derived mentoring signals: `user_intent`, `mentoring_mode`, `reveal_authorized`
- data inputs: `tool_arguments`, `prior_hint_context`, `task_context`
- provenance: `trusted_context`, `untrusted_user_content_present`

## Trust Boundaries

Trusted:

- server-generated request and trace IDs
- resolved principal identity
- registered tool metadata
- server-selected capability
- semantic policy version

Conditionally trusted:

- deterministic classifier output
- learner-state inference
- retrieved memory
- prior workflow output

Untrusted:

- user prompt
- problem statement
- submitted code
- retrieved arbitrary text
- future model-generated tool arguments
- future external tool output

Untrusted content cannot redefine policy, caller identity, principal identity, tool permissions, operation type, mentoring mode, or reveal authorization.

## Decision Model

Phase 19 supports:

- `allow`
- `deny`

`ALLOW_WITH_CONSTRAINTS` is deferred because the current runtime has no reliable constraint executor.

Decision payloads include:

- `decision`
- `policy_layer`
- `reason_code`
- `reason`
- `policy_id`
- `policy_version`
- `constraints`
- `evidence`
- `provenance`
- `injection_suspected`
- `reveal_authorized`
- `selected_capability`
- `user_intent`
- `mentoring_mode`

## Reason Taxonomy

Deny-oriented reason codes:

- `INTENT_TOOL_MISMATCH`
- `CAPABILITY_TOOL_MISMATCH`
- `MENTORING_MODE_VIOLATION`
- `SOLUTION_LEAKAGE_RISK`
- `EXPLICIT_REVEAL_NOT_AUTHORIZED`
- `PROMPT_INJECTION_SUSPECTED`
- `INSTRUCTION_OVERRIDE_ATTEMPT`
- `TOOL_ARGUMENT_SEMANTIC_MISMATCH`
- `UNSUPPORTED_TASK`
- `CAPABILITY_DRIFT`
- `UNTRUSTED_CONTEXT_POLICY_OVERRIDE`
- `INSUFFICIENT_CONTEXT`
- `POLICY_CONTEXT_INVALID`

Allow-oriented reason codes:

- `INTENT_ALIGNED`
- `CAPABILITY_ALIGNED`
- `EXPLICIT_REVEAL_AUTHORIZED`
- `SAFE_READ_OPERATION`
- `BOUNDED_ANALYSIS_ALLOWED`

## Composition Order

1. Tool existence.
2. Structural caller and operation authorization.
3. Input schema validation.
4. Semantic context validation.
5. Prompt-injection / instruction-override suspicion.
6. Capability-to-tool alignment.
7. Intent-to-tool alignment.
8. Mentoring-mode-to-tool alignment.
9. Explicit reveal / solution-leakage boundary.
10. Tool-argument semantic validation.
11. Tool execution.
12. Output validation.
13. Trajectory and persistence evidence.

## Precedence

- structural deny > semantic allow
- act deny default > model request
- trusted runtime metadata > untrusted user text
- explicit reveal authorization > model-generated argument
- semantic deny > raw legacy fallback in governed runtime path

## Failure Behavior

The gateway fails closed on invalid semantic context, structural deny, unauthorized reveal escalation, and prompt-injection-like policy override pressure. The `/mentor/route` path may return a safe non-tool fallback, but it must not call the same denied raw tool directly.

## Current Limitations

- Obvious injection-pattern detection only; no claim of complete prompt-injection mitigation.
- Current policy maps only the registered gateway tools.
- Legacy direct endpoints are documented but not fully migrated.
- No live Gemini/ADK tool invocation is enabled.
