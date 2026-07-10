# Phase 27 Completion Report: PostgreSQL + Production Auth Boundary

Status: Complete
Owner: AlgoFlow
Date: 2026-07-10

## Objective

Move AlgoFlow closer to production readiness by replacing trusted-header-only production assumptions with a real local-verifiable auth boundary and by making PostgreSQL/migration-managed startup explicit. Preserve local demo behavior and accepted deterministic baselines.

## Architecture Changes

- Added `backend/app/core/auth_tokens.py` for signed HMAC bearer tokens.
- Updated `get_principal`:
  - local mode still supports `x-user-id`, `x-authenticated-user-id`, or `demo-user`
  - production-like `AUTH_MODE=hmac` requires `Authorization: Bearer <token>`
  - production-like trusted-header mode requires `AUTH_MODE=trusted_header` and `TRUSTED_HEADER_AUTH_ENABLED=true`
- Added production config guards:
  - reject SQLite in production-like environments
  - require `postgresql+asyncpg://` URLs
  - require `AUTO_CREATE_DB_SCHEMA=false`
  - require `AUTH_TOKEN_SECRET` for HMAC auth
  - reject unrecognized production auth modes
- Updated `init_db` so `AUTO_CREATE_DB_SCHEMA=false` skips startup `create_all`.
- Added `asyncpg` backend dependency.

## Runtime Paths

Local request identity:

```text
ENVIRONMENT=local
  -> x-authenticated-user-id or x-user-id or demo-user
  -> Principal(auth_mode=local-demo)
```

Production-like HMAC request identity:

```text
ENVIRONMENT=production
AUTH_MODE=hmac
Authorization: Bearer <signed-token>
  -> verify HMAC signature
  -> verify version, subject, expiration
  -> Principal(auth_mode=hmac-bearer)
```

Production-like trusted-header identity:

```text
ENVIRONMENT=production
AUTH_MODE=trusted_header
TRUSTED_HEADER_AUTH_ENABLED=true
x-authenticated-user-id: <gateway-user-id>
  -> Principal(auth_mode=trusted-header)
```

Database startup:

```text
AUTO_CREATE_DB_SCHEMA=true
  -> local/dev create_all startup path

AUTO_CREATE_DB_SCHEMA=false
  -> production-like migration-managed schema path
  -> init_db returns without create_all
```

## Verification Results

Focused tests:

```text
cd backend && .venv/bin/pytest -q tests/test_identity_policy.py tests/test_api_contracts.py tests/test_memory_context.py
16 passed, 5 warnings
```

Lint:

```text
cd backend && .venv/bin/ruff check app tests
All checks passed
```

Full verification was run after documentation updates and is summarized in the final phase handoff.

Full backend tests:

```text
cd backend && .venv/bin/pytest -q
106 passed, 5 warnings
```

Explicit evaluations:

```text
adk_routing: 7 passed / 7
adk_tool_orchestration: 9 passed / 9
semantic_tool_policy: 19 passed / 19
suite all: 66 passed / 66
```

Accepted deterministic baseline:

```text
status: pass
current_run_id: eval_20260710T084539Z_5578b842
caseset_drift: false for code_review, hinting, pattern_transfer, problem_intelligence
blocking_regressions: []
warnings: []
```

Frontend build:

```text
cd frontend && node node_modules/next/dist/bin/next build
Compiled successfully
Generated 12 static pages
```

## Baseline Impact

Local defaults remain compatible with existing tests and frontend development. Production-like environments now fail closed unless PostgreSQL, migration-managed startup, and auth mode are configured.

## Known Limitations

- HMAC bearer auth is a controlled production/staging boundary, not a full OAuth/OIDC provider.
- Alembic migration files are not yet generated.
- Cloud SQL, Secret Manager, Docker, CI/CD, and deployment smoke tests remain part of the later deployment-hardening phase.
- Existing schemas still include `user_id` for local compatibility, but service routes use the resolved principal for data ownership.
