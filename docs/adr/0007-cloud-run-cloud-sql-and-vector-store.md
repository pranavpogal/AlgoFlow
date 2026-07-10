# ADR 0007: Cloud Deployment Baseline

Status: Proposed

## Context

Current repo has Dockerfiles and Compose but uses local SQLite/Chroma defaults and no CI/CD/IaC. The target is Google Cloud but not unnecessary complexity.

## Decision

Prefer Cloud Run for frontend/backend/agent runtime initially, Cloud SQL PostgreSQL for structured state, Secret Manager for secrets, Artifact Registry for images, Cloud Logging/Monitoring/Trace for observability, and pgvector or Chroma-managed service for vector retrieval until scale justifies Vertex AI Vector Search.

## Alternatives

- GKE: rejected until requirements justify Kubernetes.
- Deploy entire application on Vertex AI: rejected; only model inference/agent integrations need Vertex/Gemini.
- Vertex AI Vector Search immediately: deferred.

## Consequences

- Services must be stateless.
- Local filesystem persistence must be dev-only.
- Migrations and connection pooling are required.

## Security Impact

Requires least-privilege service accounts and no secrets in images/prompts/logs.

## Operational Impact

Cloud Run is simpler than GKE but still needs CI/CD, health checks, and rollback.

## Evaluation Impact

Deployment smoke tests and production-like eval smoke suites required.
