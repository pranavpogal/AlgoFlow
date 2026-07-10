# PostgreSQL + Production Auth Runtime Audit

Status: Current-state audit before Phase 27 implementation
Owner: AlgoFlow
Date: 2026-07-10

## Current Database State

Local runtime defaults to:

```text
sqlite+aiosqlite:///./algoflow.db
```

`Settings.validate_runtime_config()` already rejects SQLite in production-like environments. SQLAlchemy models use mostly portable types (`String`, `Text`, `JSON`, `DateTime`) and async sessions are created through `create_async_engine`.

## Gap

The backend package currently depends on `aiosqlite` but not a PostgreSQL async driver. There is no explicit PostgreSQL URL validation, migration guidance, or startup distinction between local `create_all` and production migration-managed schema creation.

## Current Auth State

`get_principal` currently supports:

- local mode: `x-authenticated-user-id`, `x-user-id`, or `demo-user`
- production-like mode: required `x-authenticated-user-id`

This is safer than trusting request body `user_id`, but production-like auth still relies on a trusted header. That is acceptable only behind a separately authenticated gateway, and the current repo does not enforce a real bearer/session token boundary.

## Proposed Narrow Slice

Add a production-ready local-verifiable auth boundary without introducing a full OAuth provider:

- local mode remains convenient for demo and tests
- production-like mode defaults to HMAC bearer token auth
- trusted-header auth is allowed only when explicitly configured
- user ID continues to come from resolved principal, not request body
- analytics/user-scoped routes continue enforcing same-user access

Add PostgreSQL readiness:

- include `asyncpg` dependency
- validate production-like `DATABASE_URL` uses an async PostgreSQL dialect
- document migration-managed production startup expectations
- keep local SQLite defaults unchanged

## Non-Goals

- No OAuth/OIDC provider integration.
- No Alembic migration generation in this slice.
- No Cloud SQL deployment or Docker hardening.
- No schema rewrite or data migration.

## Expected Tests

- production-like config rejects SQLite
- production-like auth requires bearer token by default
- valid HMAC bearer token resolves principal
- malformed/invalid token fails closed
- trusted-header mode works only when explicitly configured
- local header/demo behavior remains unchanged

## Known Limitations

- HMAC bearer tokens are a deployable boundary for controlled demos/staging, not a replacement for managed OAuth/OIDC.
- Production schema management still requires Alembic or an external migration process.
