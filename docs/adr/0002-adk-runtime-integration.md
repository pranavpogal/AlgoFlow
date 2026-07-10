# ADR 0002: Real Google ADK Runtime Integration

Status: Proposed

## Context

`google-adk 2.2.0` is installed and agents are defined, but no ADK Runner/session/event path is invoked by API routes.

## Decision

Do not bolt ADK into every endpoint immediately. First establish typed task context, request IDs, policy checks, tool contracts, and eval fixtures. Then introduce a bounded ADK runtime wrapper for routes where autonomous coordination adds value.

## Alternatives

- Immediate ADK invocation for every request: rejected due lack of observability, policy, and evals.
- Never use ADK: rejected because the project goal includes serious ADK agent orchestration.

## Consequences

- Phase 3 will add runner lifecycle, sessions, events, bounded steps, structured output validation, and trace propagation.
- Deterministic fallbacks remain for local and test execution.

## Security Impact

ADK agents must receive scoped tools only through a gateway.

## Operational Impact

Adds model latency/cost; requires timeout and retry policy.

## Evaluation Impact

Trajectory evals must verify delegation, tool choice, and failure handling, not only final text.
