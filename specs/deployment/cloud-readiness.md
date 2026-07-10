# Cloud Readiness Specification

Status: Partially Implemented
Owner: AlgoFlow
Phase: 1

## Purpose

Define production deployment direction without prematurely adding cloud complexity.

## Target Direction

- Frontend: Cloud Run or managed frontend platform.
- Backend: Cloud Run.
- Agent runtime: Cloud Run initially, integrated with Gemini/Vertex AI as needed.
- Database: Cloud SQL PostgreSQL.
- Vector: PostgreSQL + pgvector initially unless scale justifies Vertex AI Vector Search.
- Secrets: Secret Manager.
- Artifacts: Artifact Registry and Cloud Storage for eval artifacts if needed.
- Observability: Cloud Logging, Monitoring, Trace with OpenTelemetry-compatible instrumentation.

## Non-Goals

- GKE unless requirements justify Kubernetes.
- Deploying the entire app on Vertex AI.
- Terraform before architecture and service boundaries stabilize.

## Requirements

- Services are stateless.
- Durable state is externalized.
- Production config rejects local SQLite/Chroma defaults unless explicitly allowed.
- Production config requires an async PostgreSQL URL: `postgresql+asyncpg://...`.
- Production config disables startup `create_all`; schema creation is migration-managed.
- Production-like auth requires HMAC bearer tokens unless trusted-header mode is explicitly enabled behind an authenticated gateway.
- Secrets are never baked into images.
- Health/readiness endpoints exist.
- CI/CD supports smoke tests and rollback.

## BDD Scenarios

### Scenario: Production Starts With Local SQLite

Given environment is production
And `DATABASE_URL` points to local SQLite
When backend starts
Then startup fails with a clear configuration error

### Scenario: Production Starts With Sync PostgreSQL URL

Given environment is production
And `DATABASE_URL` starts with `postgresql://`
When backend configuration is validated
Then startup fails and requires `postgresql+asyncpg://`

### Scenario: Production Starts With Startup Create All

Given environment is production
And `AUTO_CREATE_DB_SCHEMA=true`
When backend configuration is validated
Then startup fails because migrations must manage schema creation

### Scenario: Production Request Without Bearer Token

Given environment is production
And `AUTH_MODE=hmac`
When a request omits `Authorization: Bearer ...`
Then the API returns an authentication error

### Scenario: Secret Missing

Given live ADK/Gemini mode is enabled
And no model credentials are configured
When the app starts or model path is invoked
Then the system fails safely or falls back according to environment policy

## Testing Strategy

- Config validation tests.
- Container build tests.
- Smoke endpoint tests.

## Acceptance Criteria

- Deployment docs distinguish local, staging, and production.
- Cloud target architecture avoids unnecessary GKE/Vertex overreach.
- Production unsafe local persistence is gated.
- Production-like auth does not rely on client-supplied `user_id`.
