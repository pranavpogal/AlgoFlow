#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:?Set BACKEND_URL to the deployed backend Cloud Run URL.}"

curl -fsS "${BACKEND_URL}/api/v1/health"
echo
curl -fsS "${BACKEND_URL}/api/v1/diagnostics/gemini"
echo
curl -fsS \
  -H "content-type: application/json" \
  -d '{"title":"House Robber","description":"You are given an integer array nums where nums[i] represents the amount of money in the ith house. You cannot rob adjacent houses. Return the maximum amount you can rob."}' \
  "${BACKEND_URL}/api/v1/problems/analyze"
echo
