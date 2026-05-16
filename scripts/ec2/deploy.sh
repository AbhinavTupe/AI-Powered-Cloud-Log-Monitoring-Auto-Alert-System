#!/usr/bin/env bash
set -Eeuo pipefail

# Run this on the EC2 instance after SSH to pull the latest code and restart
# the production container. It gives a simple, interview-friendly deployment
# workflow without adding Kubernetes or managed services.

APP_DIR="${APP_DIR:-/opt/cloud-log-monitoring}"
BRANCH="${BRANCH:-main}"

cd "$APP_DIR"

git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

if [ ! -f .env ]; then
  cp .env.example .env
fi

docker compose -f docker-compose.prod.yml up -d --build
docker image prune -f

docker compose -f docker-compose.prod.yml ps
curl --retry 10 --retry-delay 3 --fail http://localhost/health

