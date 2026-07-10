# API Design

Base path: `/api/v1`

## Current Endpoints

- `GET /health`: service health.
- `POST /mentor/route`: narrow ADK coordinator routing slice for problem analysis and next-hint requests. It returns the selected deterministic workflow result plus a `trajectory-v1` trace. Live ADK model invocation remains disabled by default.
- `GET /agent-trajectories/{trajectory_id}`: retrieves a stored ADK/runtime trajectory for the resolved principal.
- `GET /agent-trajectories/{trajectory_id}/policy-decisions`: retrieves persisted policy-decision records for gateway-mediated tool calls tied to a stored trajectory and resolved principal.
- `POST /problems/analyze`: deterministic Problem Intelligence Skill with typed taxonomy, evidence, confidence, provenance, and prerequisite extraction.
- `POST /hints/next`: deterministic progressive-hinting Skill with intent detection, previous-hint awareness, leakage controls, and structured learning evidence.
- `POST /code-review`: deterministic Code Review Skill with review-intent detection, Python AST-backed findings, limited non-Python text checks, and structured finding evidence.
- `POST /study-plan`: deterministic study-plan generation from current memory snapshot.
- `POST /recommendations`: learner-scoped structural transfer recommendations with confidence, evidence, and fallback metadata.
- `POST /pattern-transfer`: deterministic Pattern Transfer Skill with transfer taxonomy, structural bridge explanations, and learner-evidence grounding.
- `GET /analytics/{user_id}`: readiness, readiness components, mastery, topic risk, mistake trends, learning velocity, mock-interview readiness, next best actions, and limitations derived from current memory and learning-event evidence.
- `POST /mock-interview/turn`: stateful deterministic mock-interview workflow with transcript persistence, persona style, rubric scorecard, stage tracking, and memory-aware feedback.

## Current Identity Boundary

Routes resolve a principal before service code runs, and write workflows ignore request body `user_id`. Local development remains convenient, but production-like environments now fail closed unless an explicit auth mode is configured.

## Current Request Boundary Foundation

Phase 2 added:

- `x-request-id` response header.
- `x-trace-id` response header.
- Safe validation error envelope for malformed requests.
- Safe internal error envelope for unexpected exceptions.
- Local-safe principal resolution.
- Same-user policy enforcement for analytics reads.

Successful response bodies remain backward-compatible with the frontend.

Local development behavior:

- If no auth header is provided, the backend resolves the request as `demo-user`.
- `x-user-id` or `x-authenticated-user-id` may be used for local testing.
- Request body `user_id` is ignored by write workflows in favor of the resolved principal.

Production-like behavior:

- Default production-like mode is HMAC bearer authentication via `Authorization: Bearer <token>`.
- `AUTH_TOKEN_SECRET` is required for HMAC bearer authentication.
- `x-authenticated-user-id` trusted-header mode is allowed only when `AUTH_MODE=trusted_header` and `TRUSTED_HEADER_AUTH_ENABLED=true`.
- Client-supplied body `user_id` must not determine data ownership.
- Cross-user analytics access returns `FORBIDDEN`.
- OAuth/OIDC is still a future enhancement; HMAC bearer auth is a deployable boundary for controlled demos/staging, not a managed identity provider.

Learning evidence:

- Existing workflows now append compact `learning_events` records for classification, hints, code review, study-plan generation, analytics views, and interview turns.
- Events intentionally avoid storing full submitted code in event evidence; code remains in the existing `problem_attempts` review path for now.
- No public event API exists yet.
- Code review now records `CodeReviewRequested`, `CodeReviewCompleted`, and `CodeFindingProduced` events with confidence/provenance-backed evidence.
- Problem analysis now records `ProblemClassified`, `PatternDetected`, and `StructuralCueDetected` events as classification-only evidence, not mastery proof.
- Pattern transfer now records `PatternTransferRequested` and `PatternTransferRecommended` events as recommendation evidence, not mastery proof.

Policy-decision evidence:

- The narrow `/mentor/route` runtime path persists gateway policy decisions for `problem.detect_pattern` tool calls.
- Policy records preserve request, trace, session, trajectory, tool, caller, operation, risk, decision, policy ID, success, error, latency, and scoped metadata.
- Phase 19 policy metadata also includes `structural_decision`, `semantic_decision`, semantic policy version, semantic reason code, selected capability, user intent, mentoring mode, reveal authorization, and injection suspicion where available.
- The policy-decision read endpoint is principal-scoped and trajectory-scoped; there is no broad admin policy-log API yet.

Learner intelligence:

- Analytics now derives readiness, readiness components, strong topics, weak topics, topic mastery, topic risk, mistake trends, learning velocity, mock-interview readiness, next best actions, confidence, and evidence counts from attempts, mistakes, learning events, and interview scorecards.
- Passive events such as `AnalyticsViewed` do not increase mastery confidence.
- New users no longer receive fabricated strong or weak topics in analytics.
- Analytics limitations are returned explicitly so scores are not presented as guarantees of interview performance.

## Target Contract Direction

See [specs/api/api-contracts.md](../specs/api/api-contracts.md).

Target additions:

- request IDs
- trace IDs
- consistent error envelopes
- auth-derived identity
- input size limits
- policy denial responses
- structured failure categories

## Target Error Envelope

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Safe human-readable message",
    "details": {},
    "retryable": false
  },
  "request_id": "req_...",
  "trace_id": "trace_..."
}
```
