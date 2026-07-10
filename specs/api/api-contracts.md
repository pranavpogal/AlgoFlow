# API Contracts Specification

Status: Draft
Owner: AlgoFlow
Phase: 1

## Purpose

Define stable API contract foundations for request identity, response envelopes, errors, authentication-derived user identity, and schema compatibility.

## Motivation

Current routes return typed success payloads but lack consistent request IDs, error envelopes, auth boundaries, pagination conventions, and failure semantics. Client code currently sends `user_id`, which is unacceptable for production multi-user behavior.

## Scope

- API versioning under `/api/v1`.
- Request ID and trace ID propagation.
- Success and error response conventions.
- Authenticated user identity rules.
- Input validation and size limits.
- Compatibility rules for frontend consumers.

## Non-Goals

- Implementing OAuth/OIDC in this spec.
- Rewriting every endpoint immediately.
- Streaming protocol design.

## User Stories

- As a frontend client, I can display a clear error without parsing raw server exceptions.
- As an engineer, I can trace one request across API, tools, memory, and agent/runtime components.
- As a security reviewer, I can verify that user identity comes from authentication, not request bodies.

## API Contract

### Request Metadata

Every request SHOULD have:

- `X-Request-ID`: client-provided or server-generated unique ID.
- `X-Trace-ID`: server-generated trace ID if not already present from infrastructure.
- Authenticated user context from session/token middleware.

### Success Envelope

For Phase 1, existing response bodies may remain unchanged. Phase 2 should introduce an optional envelope for new endpoints:

```json
{
  "data": {},
  "request_id": "req_...",
  "trace_id": "trace_..."
}
```

### Error Envelope

All controlled failures SHOULD return:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable safe message",
    "details": {},
    "retryable": false
  },
  "request_id": "req_...",
  "trace_id": "trace_..."
}
```

Error codes:

- `VALIDATION_ERROR`
- `AUTH_REQUIRED`
- `FORBIDDEN`
- `NOT_FOUND`
- `POLICY_DENIED`
- `RATE_LIMITED`
- `MODEL_TIMEOUT`
- `TOOL_TIMEOUT`
- `RETRIEVAL_FAILED`
- `INTERNAL_ERROR`

## Identity Rule

Production endpoints MUST derive `user_id` from authenticated context. Client-supplied `user_id` is allowed only in local demo mode and must be rejected or ignored in production.

## Security

- Do not echo secrets, raw stack traces, or hidden prompts.
- Enforce request body size limits.
- Validate all payloads through Pydantic schemas.
- Treat problem statements, code, and retrieved content as untrusted.

## Observability

- Log request method, route template, status, request ID, trace ID, latency, and failure category.
- Do not log full submitted code by default.

## Failure Modes

- Missing auth in production -> `AUTH_REQUIRED`.
- Client-supplied foreign user ID -> `FORBIDDEN`.
- Malformed JSON -> `VALIDATION_ERROR`.
- Unexpected exception -> `INTERNAL_ERROR` with safe message.

## BDD Scenarios

### Scenario: Controlled Validation Error

Given an API request omits required field `title`
When the request reaches `/api/v1/problems/analyze`
Then the API returns a validation error envelope
And includes request and trace identifiers
And does not expose a Python stack trace

### Scenario: Client Attempts User Spoofing

Given production mode is enabled
And authenticated user is `user_a`
When the client sends a body with `user_id` set to `user_b`
Then the server ignores or rejects the client-supplied user ID
And no state is read or written for `user_b`

### Scenario: Existing Prototype Compatibility

Given local demo mode is enabled
When the frontend sends `demo-user`
Then the endpoint may accept it for local development
And the response remains compatible with current frontend pages

## Testing Strategy

- API contract tests for success and error envelopes.
- Auth/user isolation tests once auth middleware exists.
- Pydantic validation tests for malformed payloads.

## Evaluation Strategy

Not applicable for deterministic API contract behavior, except trajectory evals should inspect request IDs across agent/tool paths.

## Rollout

1. Add middleware and error types behind compatible response behavior.
2. Update frontend to display error envelopes.
3. Enforce auth-derived identity outside local mode.

## Rollback

Disable envelope wrapping while preserving logs and request IDs.
