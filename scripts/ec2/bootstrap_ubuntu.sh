#!/usr/bin/env bash
set -Eeuo pipefail

# EC2 user data runs as root on first boot. This script installs Docker,
# clones the repo, creates an environment file, and starts the production
# Compose stack.

APP_DIR="${APP_DIR:-/opt/cloud-log-monitoring}"
APP_USER="${APP_USER:-ubuntu}"
BRANCH="${BRANCH:-main}"
REPO_URL="${REPO_URL:-https://github.com/AbhinavTupe/AI-Powered-Cloud-Log-Monitoring-Auto-Alert-System.git}"
LOG_FILE="/var/log/cloud-log-monitoring-bootstrap.log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "Starting cloud log monitoring bootstrap at $(date -Is)"

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl git

install_docker_from_official_repo() {
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc

  . /etc/os-release
  ubuntu_codename="${UBUNTU_CODENAME:-$VERSION_CODENAME}"

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${ubuntu_codename} stable" \
    > /etc/apt/sources.list.d/docker.list

  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

if ! command -v docker >/dev/null 2>&1; then
  install_docker_from_official_repo
fi

if ! docker compose version >/dev/null 2>&1; then
  install_docker_from_official_repo
fi

docker compose version

systemctl enable docker
systemctl start docker

if id "$APP_USER" >/dev/null 2>&1; then
  usermod -aG docker "$APP_USER"
fi

mkdir -p "$APP_DIR"

if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch origin "$BRANCH"
  git -C "$APP_DIR" reset --hard "origin/$BRANCH"
else
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
fi

docker compose -f docker-compose.prod.yml up -d --build
docker image prune -f

echo "Deployment status:"
docker compose -f docker-compose.prod.yml ps

echo "Health check:"
curl --retry 10 --retry-delay 3 --fail http://localhost/health

if id "$APP_USER" >/dev/null 2>&1; then
  chown -R "$APP_USER:$APP_USER" "$APP_DIR"
fi

echo "Cloud log monitoring bootstrap completed at $(date -Is)"
