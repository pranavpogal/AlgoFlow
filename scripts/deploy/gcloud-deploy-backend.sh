#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID to your Google Cloud project ID.}"
REGION="${REGION:-us-central1}"
BACKEND_SERVICE="${BACKEND_SERVICE:-algoflow-backend}"
ARTIFACT_REPOSITORY="${ARTIFACT_REPOSITORY:-algoflow}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-algoflow-cloud-run}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-http://localhost:3000}"
GEMINI_PROVIDER="${GEMINI_PROVIDER:-vertex_ai}"
GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-global}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPOSITORY}/${BACKEND_SERVICE}:latest"

gcloud builds submit . \
  --project="${PROJECT_ID}" \
  --config=deploy/cloudbuild-backend.yaml \
  --substitutions="_IMAGE=${IMAGE}"

gcloud run deploy "${BACKEND_SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${IMAGE}" \
  --allow-unauthenticated \
  --service-account="${SERVICE_ACCOUNT_EMAIL}" \
  --set-env-vars="ENVIRONMENT=demo" \
  --set-env-vars="DATABASE_URL=sqlite+aiosqlite:////tmp/algoflow.db" \
  --set-env-vars="CHROMA_PATH=/tmp/algoflow-chroma" \
  --set-env-vars="AUTO_CREATE_DB_SCHEMA=true" \
  --set-env-vars="CORS_ALLOWED_ORIGINS=${FRONTEND_ORIGIN}" \
  --set-env-vars="GEMINI_PROVIDER=${GEMINI_PROVIDER}" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-env-vars="GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION}" \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=true" \
  --set-env-vars="ENABLE_GEMINI_CLASSIFICATION=true" \
  --set-env-vars="ENABLE_GEMINI_HINTS=false" \
  --set-env-vars="ENABLE_GEMINI_CODE_REVIEW=false" \
  --set-env-vars="ENABLE_GEMINI_STUDY_PLAN=false" \
  --set-env-vars="ENABLE_GEMINI_RECOMMENDATIONS=false" \
  --set-env-vars="ENABLE_GEMINI_PATTERN_TRANSFER=false" \
  --set-env-vars="ENABLE_GEMINI_MOCK_INTERVIEW=false" \
  --set-env-vars="ENABLE_GEMINI_ANALYTICS=false" \
  --set-env-vars="GEMINI_CLASSIFICATION_TIMEOUT_SECONDS=3" \
  --set-env-vars="GEMINI_ADVISORY_TIMEOUT_SECONDS=5" \
  --set-env-vars="ENABLE_LIVE_ADK=false"

BACKEND_URL="$(gcloud run services describe "${BACKEND_SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format='value(status.url)')"

echo "Backend deployed: ${BACKEND_URL}"
echo "Health: ${BACKEND_URL}/api/v1/health"
echo "Gemini diagnostics: ${BACKEND_URL}/api/v1/diagnostics/gemini"
