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
- Cloud-demo storage is intentionally ephemeral unless a managed database/vector store is configured.

## Cloud Demo Deployment

AlgoFlow can be deployed today as a deterministic public demo without Gemini.
This mode is intended for recruiter demos and portfolio walkthroughs, not for
production multi-user persistence.

The repository includes a Render-compatible `render.yaml` with two Docker web
services:

- `algoflow-backend`
- `algoflow-frontend`

Default demo behavior:

- `ENVIRONMENT=demo`
- Gemini and live ADK model calls are disabled.
- Deterministic Skills, workflows, tool policy, trajectory capture, memory
  summaries, mock interviews, analytics, and frontend pages remain available.
- SQLite and local Chroma paths are allowed only because this is explicit demo
  mode.
- Demo storage is ephemeral on platforms without persistent disks.

After the backend service receives a public URL, configure:

```bash
NEXT_PUBLIC_API_BASE=https://<backend-service-url>/api/v1
```

After the frontend service receives a public URL, configure the backend CORS
allowlist:

```bash
CORS_ALLOWED_ORIGINS=https://<frontend-service-url>
```

Then redeploy both services.

Useful smoke checks:

```bash
curl https://<backend-service-url>/api/v1/health
curl https://<backend-service-url>/api/v1/diagnostics/gemini
```

The Gemini diagnostic should report `key_configured: false` or a controlled
Google-side error unless a working API key is configured. That should not block
the deterministic demo.

## Optional Gemini Advisory Features

Gemini can be enabled per workflow without removing deterministic fallbacks.
If Google returns a timeout, quota error, or permission error, AlgoFlow keeps
serving the deterministic response and records the fallback reason in the
response's advisory metadata.

```bash
GOOGLE_API_KEY=<working-ai-studio-key>
GEMINI_MODEL=gemini-2.5-flash
ENABLE_GEMINI_CLASSIFICATION=true
ENABLE_GEMINI_HINTS=true
ENABLE_GEMINI_CODE_REVIEW=true
ENABLE_GEMINI_STUDY_PLAN=true
ENABLE_GEMINI_RECOMMENDATIONS=true
ENABLE_GEMINI_PATTERN_TRANSFER=true
ENABLE_GEMINI_MOCK_INTERVIEW=true
ENABLE_GEMINI_ANALYTICS=true
GEMINI_ADVISORY_TIMEOUT_SECONDS=8
```

Gemini is intentionally not used to rewrite audit traces. Trace and policy
records remain deterministic evidence because they are used for debugging,
baseline comparison, and safety review.

Recommended demo setting while Google access is unreliable:

```bash
ENABLE_GEMINI_CLASSIFICATION=true
ENABLE_GEMINI_HINTS=false
ENABLE_GEMINI_CODE_REVIEW=false
ENABLE_GEMINI_STUDY_PLAN=false
ENABLE_GEMINI_RECOMMENDATIONS=false
ENABLE_GEMINI_PATTERN_TRANSFER=false
ENABLE_GEMINI_MOCK_INTERVIEW=false
ENABLE_GEMINI_ANALYTICS=false
GEMINI_CLASSIFICATION_TIMEOUT_SECONDS=3
```

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
CORS_ALLOWED_ORIGINS=https://<frontend-domain>
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
