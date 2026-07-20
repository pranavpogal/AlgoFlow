#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID to your Google Cloud project ID.}"
REGION="${REGION:-us-central1}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-algoflow-frontend}"
ARTIFACT_REPOSITORY="${ARTIFACT_REPOSITORY:-algoflow}"
BACKEND_URL="${BACKEND_URL:?Set BACKEND_URL to the deployed backend Cloud Run URL.}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPOSITORY}/${FRONTEND_SERVICE}:latest"

gcloud builds submit . \
  --project="${PROJECT_ID}" \
  --config=deploy/cloudbuild-frontend.yaml \
  --substitutions="_IMAGE=${IMAGE},_NEXT_PUBLIC_API_BASE=${BACKEND_URL}/api/v1"

gcloud run deploy "${FRONTEND_SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${IMAGE}" \
  --allow-unauthenticated \
  --set-env-vars="NEXT_PUBLIC_API_BASE=${BACKEND_URL}/api/v1"

FRONTEND_URL="$(gcloud run services describe "${FRONTEND_SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format='value(status.url)')"

echo "Frontend deployed: ${FRONTEND_URL}"
echo "Update backend CORS with:"
echo "FRONTEND_ORIGIN=${FRONTEND_URL} PROJECT_ID=${PROJECT_ID} REGION=${REGION} scripts/deploy/gcloud-deploy-backend.sh"
