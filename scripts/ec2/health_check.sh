#!/usr/bin/env bash
set -Eeuo pipefail

BASE_URL="${BASE_URL:-http://localhost}"

echo "Checking $BASE_URL/health"
curl --fail "$BASE_URL/health"
echo

echo "Checking $BASE_URL/dashboard"
curl --fail "$BASE_URL/dashboard"
echo

