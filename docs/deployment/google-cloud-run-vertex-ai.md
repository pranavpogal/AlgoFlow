# Google Cloud Run + Vertex AI Deployment

## Goal

Deploy AlgoFlow as a Google Cloud demo using:

- Cloud Run for the FastAPI backend.
- Cloud Run for the Next.js frontend.
- Cloud Build and Artifact Registry for container images.
- Vertex AI Gemini through the Google Gen AI SDK.
- Deterministic workflows as fallback.
- Demo-mode SQLite and Chroma storage initially.

This is a recruiter-ready cloud demo path. It is not the final multi-tenant
production path until Cloud SQL, durable vector memory, and real auth are wired.

## Prerequisites

- A Google Cloud project with billing enabled.
- `gcloud` installed and authenticated.
- Permission to enable APIs and create service accounts.
- Region selected, for example `us-central1`.

Required APIs:

- Cloud Run
- Cloud Build
- Artifact Registry
- Secret Manager
- Vertex AI

## Phase D1: Bootstrap Google Cloud

```bash
PROJECT_ID=<your-project-id> \
REGION=us-central1 \
scripts/deploy/gcloud-bootstrap.sh
```

This enables required services and creates:

```text
algoflow-cloud-run@<project-id>.iam.gserviceaccount.com
```

It also creates an Artifact Registry Docker repository:

```text
us-central1-docker.pkg.dev/<project-id>/algoflow
```

The service account receives:

- `roles/aiplatform.user`
- `roles/secretmanager.secretAccessor`

## Phase D2: Deploy Backend

First deploy with localhost CORS as a temporary placeholder:

```bash
PROJECT_ID=<your-project-id> \
REGION=us-central1 \
FRONTEND_ORIGIN=http://localhost:3000 \
scripts/deploy/gcloud-deploy-backend.sh
```

Save the printed backend URL:

```text
https://algoflow-backend-....run.app
```

Backend defaults:

- `ENVIRONMENT=demo`
- `GEMINI_PROVIDER=vertex_ai`
- `GOOGLE_CLOUD_PROJECT=<project-id>`
- `GOOGLE_CLOUD_LOCATION=global`
- `GOOGLE_GENAI_USE_VERTEXAI=true`
- `ENABLE_GEMINI_CLASSIFICATION=true`
- advisory Gemini flags disabled initially
- deterministic fallback preserved

The script builds the backend image with Cloud Build using
`deploy/cloudbuild-backend.yaml`, pushes it to Artifact Registry, then deploys
that image to Cloud Run.

## Phase D3: Deploy Frontend

```bash
PROJECT_ID=<your-project-id> \
REGION=us-central1 \
BACKEND_URL=https://<backend-service-url> \
scripts/deploy/gcloud-deploy-frontend.sh
```

Save the printed frontend URL:

```text
https://algoflow-frontend-....run.app
```

## Phase D4: Update Backend CORS

Redeploy the backend with the real frontend origin:

```bash
PROJECT_ID=<your-project-id> \
REGION=us-central1 \
FRONTEND_ORIGIN=https://<frontend-service-url> \
scripts/deploy/gcloud-deploy-backend.sh
```

## Phase D5: Smoke Test

```bash
BACKEND_URL=https://<backend-service-url> \
scripts/deploy/gcloud-smoke-test.sh
```

Also open:

```text
https://<frontend-service-url>
https://<backend-service-url>/api/v1/diagnostics/gemini
```

Expected diagnostic shape:

```json
{
  "provider": "vertex_ai",
  "auth_configured": true,
  "google_cloud_project_configured": true,
  "ok": true
}
```

If `ok` is false, the app still works through deterministic fallback. Check:

- Vertex AI API enabled.
- Cloud Run service account has `roles/aiplatform.user`.
- Billing is enabled.
- `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` are correct.

## Optional Gemini Flags

Start with classification first:

```bash
ENABLE_GEMINI_CLASSIFICATION=true
ENABLE_GEMINI_HINTS=false
ENABLE_GEMINI_CODE_REVIEW=false
ENABLE_GEMINI_STUDY_PLAN=false
ENABLE_GEMINI_RECOMMENDATIONS=false
ENABLE_GEMINI_PATTERN_TRANSFER=false
ENABLE_GEMINI_MOCK_INTERVIEW=false
ENABLE_GEMINI_ANALYTICS=false
```

After diagnostics pass, enable advisory flags gradually.

## Why Vertex AI

Vertex AI gives the deployment a cleaner Google Cloud production story:

- IAM-based service-account authentication.
- No AI Studio API key dependency for Cloud Run.
- Centralized Google Cloud project/billing controls.
- Better resume signal for applied AI engineering.

## Current Limitations

- Demo storage is ephemeral.
- No Cloud SQL production persistence yet.
- No OIDC/login user flow yet.
- Gemini is advisory/adjudication-based, not an unchecked agent.
- Trace and policy records stay deterministic by design.
The script builds the frontend image with Cloud Build using
`deploy/cloudbuild-frontend.yaml`. `NEXT_PUBLIC_API_BASE` is passed as a Docker
build argument so the static Next.js bundle points at the deployed backend
instead of localhost.
