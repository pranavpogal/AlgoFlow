# Google Cloud + Vertex AI Deployment Readiness Report

## Purpose

Prepare AlgoFlow for a Google Cloud demo deployment that can use Vertex AI
Gemini while preserving deterministic fallback behavior.

## Before

- Gemini used AI Studio API-key style client construction.
- Diagnostics assumed `GOOGLE_API_KEY`.
- Cloud deployment docs were generic.
- Frontend deployment risked baking a localhost backend URL.

## After

- Added `GEMINI_PROVIDER=ai_studio|vertex_ai`.
- Added `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`.
- Added a shared provider-aware Gemini client factory.
- Updated classification, hints, advisory overlays, and diagnostics to use the
  shared provider path.
- Added Google Cloud Run + Vertex AI deployment guide.
- Added Cloud Build configs for backend/frontend images.
- Added `gcloud` scripts for bootstrap, backend deploy, frontend deploy, and
  smoke testing.

## Runtime Model

Vertex AI mode uses:

```text
Cloud Run service account
  -> IAM roles/aiplatform.user
  -> Google Gen AI SDK
  -> Vertex AI Gemini
```

AI Studio mode remains available for local experiments:

```text
GOOGLE_API_KEY
  -> Google Gen AI SDK
  -> Gemini Developer API
```

## Safety

- Deterministic workflows remain available.
- Gemini failures return fallback metadata instead of failing API requests.
- Trace and policy records remain deterministic.
- CI tests mock provider behavior and do not call real Gemini/Vertex services.

## Deployment Assets

- `deploy/cloudbuild-backend.yaml`
- `deploy/cloudbuild-frontend.yaml`
- `scripts/deploy/gcloud-bootstrap.sh`
- `scripts/deploy/gcloud-deploy-backend.sh`
- `scripts/deploy/gcloud-deploy-frontend.sh`
- `scripts/deploy/gcloud-smoke-test.sh`
- `docs/deployment/google-cloud-run-vertex-ai.md`

## Remaining Before Actual Deploy

- User supplies `PROJECT_ID`.
- User authenticates `gcloud`.
- Billing must be enabled.
- Vertex AI API access must be available for the project.
- Run bootstrap, backend deploy, frontend deploy, backend CORS update, smoke
  test.
