# Deployment Strategy

## Current Local Development

Run FastAPI and Next.js separately:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --reload-dir app
```

```bash
cd frontend
npm run dev
```

Current persistence defaults are local SQLite and local ChromaDB path. These are development defaults only.

## Current Deployment Limitations

- No OAuth/OIDC provider integration.
- No Alembic migration files yet.
- No CI/CD.
- No Secret Manager integration.
- No Cloud SQL config.
- No OpenTelemetry/Cloud Trace integration.
- Frontend Dockerfile runs development server.

## Production-Like Backend Configuration

Production-like environments must not use local SQLite or startup `create_all`.

Required baseline settings:

```bash
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/algoflow
AUTO_CREATE_DB_SCHEMA=false
CHROMA_PATH=managed-chroma
AUTH_MODE=hmac
AUTH_TOKEN_SECRET=<long-random-secret>
```

Trusted-header mode is available only for deployments behind a separately authenticated gateway:

```bash
AUTH_MODE=trusted_header
TRUSTED_HEADER_AUTH_ENABLED=true
```

In that mode the gateway must set `x-authenticated-user-id`; public clients must not be allowed to spoof it.

## Target Google Cloud Direction

See [specs/deployment/cloud-readiness.md](../specs/deployment/cloud-readiness.md).

Preferred initial target:

- Frontend: Cloud Run or managed frontend platform.
- Backend: Cloud Run.
- Agent runtime: Cloud Run initially, with Gemini/Vertex AI for model calls where justified.
- Relational persistence: Cloud SQL PostgreSQL.
- Vector retrieval: PostgreSQL + pgvector initially unless scale justifies Vertex AI Vector Search.
- Secrets: Secret Manager.
- Images: Artifact Registry.
- Observability: Cloud Logging, Monitoring, Trace with OpenTelemetry-compatible instrumentation.
- Async work: Cloud Tasks or Pub/Sub only when semantics justify it.

## Non-Goals For Initial Deployment

- GKE unless requirements justify Kubernetes.
- Deploying the entire application on Vertex AI.
- Adding Terraform before service boundaries stabilize.

## Required Before Production

- Auth-derived user identity.
- Policy gateway for user-scoped data and tools.
- Request/trace IDs.
- Structured error handling.
- Config validation rejecting local SQLite, non-asyncpg PostgreSQL URLs, local Chroma, and startup schema creation in production.
- CI/CD quality gates.
- Security and evaluation smoke tests.
