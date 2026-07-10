# AlgoFlow Threat Model

Date: 2026-07-05

## Scope

This threat model covers the AlgoFlow web app, FastAPI backend, agent/Skill runtime, tool gateway, memory stores, future code execution service, evaluation pipeline, and cloud deployment path.

## Assets

- User identity and session data.
- Learner profile, mistakes, submissions, interview transcripts, and recommendations.
- Problem statements, code submissions, and feedback.
- Model prompts, Skill instructions, tool contracts, and evaluation datasets.
- Google API/Vertex credentials and database credentials.
- Agent/tool traces and logs.

## Trust Boundaries

- Browser to API.
- API to auth/session service.
- API/runtime to database/vector store.
- Agent/runtime to tool gateway.
- Tool gateway to external services.
- API/runtime to execution service.
- Execution service to sandbox.
- Retrieved memory/context to model prompt.

## Primary Threats

| Threat | Current Exposure | Target Control | Priority |
|---|---|---|---|
| IDOR via client-supplied `user_id` | Reduced: write routes now use resolved principal, but schemas still include demo `user_id` and full auth is not implemented | Auth-derived user IDs; ignore client user IDs; authorization checks | P0 |
| Cross-user memory leakage | High if deployed multi-user | Tenant-scoped DB/vector queries; policy gateway; tests | P0 |
| Prompt injection from problem statements | Medium now, high with live LLM | Trusted/untrusted context separation; instruction hierarchy; semantic policy | P1 |
| Indirect prompt injection from retrieved memory | Future high | Retrieval provenance; retrieved content cannot override system/policy | P1 |
| Arbitrary code execution | Future critical | Never execute in FastAPI; isolated sandbox with limits; disabled stub first | P0 |
| Secret leakage to prompts/logs | Medium future | Secret Manager; redaction; no credentials in prompts; logging filters | P0 |
| Tool abuse by agents | Future high | Tool gateway; least privilege; structural/semantic gating | P1 |
| Denial of service via oversized code/problem input | Medium | Request size limits; timeouts; output caps | P1 |
| Model cost explosion | Future medium | model routing; token budgets; circuit breakers | P2 |
| Misleading learner state | Current high product integrity risk | Evidence-based learning events and confidence | P0 |
| Unsafe persistent mutation | Medium | read/draft/act classification; checkpoint/rollback for high impact | P1 |
| Dependency supply chain risk | Medium | lockfiles, scans, controlled installs | P2 |

## Current Security Findings

- No production OAuth/OIDC authentication provider exists yet.
- Phase 2 adds local-safe principal resolution and production-like `x-authenticated-user-id` enforcement.
- Request body `user_id` is no longer trusted by write workflows; routes pass the resolved principal user instead.
- Analytics now enforces same-user access.
- Memory writes still need a fuller policy gateway and audit record.
- No input size limits are enforced by schemas.
- A basic centralized error envelope exists for validation/internal errors; broader redaction policy still needs to mature.
- No code execution exists, which avoids immediate RCE, but no safe architecture is ready for future execution.
- Chroma metadata is scoped by resolved `user_id`, but production-grade auth and vector access policy still need to replace trusted-header scaffolding.

## Required Controls

### Structural Gating

- Route-level auth/session dependency.
- Authenticated user must own requested resource.
- Agent/Skill can access only declared tools.
- Tool gateway validates args/results.
- Environment-gated production restrictions.
- Production config rejects local SQLite/Chroma unless explicitly allowed.

### Semantic Gating

- Check that action matches user intent.
- Prevent “one hint” from producing full solution.
- Treat user/retrieved content as untrusted.
- Detect suspicious instructions in problem statements or memory.

### Code Execution Controls

- FastAPI never executes user code.
- Execution requests go to isolated worker/sandbox.
- Limits: CPU, memory, wall-clock, process count, filesystem, network disabled, output size.
- No inherited secrets/cloud credentials.
- Ephemeral cleanup.

## Security Test Plan

- Changing `user_id` cannot read or mutate another user's records.
- Oversized inputs return controlled 413/422-style errors.
- Tool gateway denies unauthorized tool/agent combinations.
- Prompt-injection fixtures do not override hint/review instructions.
- Code execution endpoints return disabled/policy-denied until sandbox exists.
- Logs do not include secrets.
