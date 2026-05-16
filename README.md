# AI-Powered Cloud Log Monitoring & Auto-Alert System

A production-style Flask monitoring platform that ingests application logs, detects abnormal patterns, stores events in SQLite, and triggers alerts through optional Slack or email integrations.

This project is designed for a Cloud/DevOps internship portfolio: it is modular, Dockerized, CI/CD ready, AWS EC2 deployment-ready, and explainable in an interview without requiring Kubernetes or a large cloud bill.

## Architecture Overview

```text
Application / Generator
        |
        v
Flask REST API (/logs)
        |
        v
Log Processor  ---> SQLite logs table
        |
        v
Anomaly Detector
        |
        v
Alert Handler ---> SQLite alerts table ---> Slack / Email notification
        |
        v
Dashboard APIs (/logs, /alerts, /dashboard)
```

## Main Components

- `app/routes/` exposes REST endpoints for health checks, log ingestion, alert retrieval, and dashboard summaries.
- `app/services/log_processor.py` validates incoming log events and stores them.
- `app/services/anomaly_detector.py` detects `ERROR`, `FAILED`, `TIMEOUT`, repeated failures, and high-frequency events.
- `app/services/alert_handler.py` persists alerts and optionally sends Slack or email notifications.
- `app/services/log_generator.py` simulates real application logs for demos and testing.
- `scripts/ec2/` contains EC2 bootstrap, deployment, and health-check scripts.

## Features

- Flask backend service with clean app factory structure
- REST endpoints:
  - `GET /health`
  - `GET /logs`
  - `POST /logs`
  - `GET /alerts`
  - `PATCH /alerts/<id>/resolve`
  - `GET /dashboard`
- Simulated application log generator
- Log ingestion pipeline with validation and normalization
- Rule-based intelligent anomaly detection
- Auto alert creation with cooldown support
- SQLite persistence for logs and alerts
- Dashboard-style API summaries
- Docker and Docker Compose support
- GitHub Actions CI pipeline
- AWS EC2 production deployment assets

## Project Structure

```text
.
|-- app/
|   |-- routes/
|   |-- services/
|   |-- utils/
|   |-- config.py
|   `-- database.py
|-- scripts/
|   |-- ec2/
|   |   |-- bootstrap_ubuntu.sh
|   |   |-- deploy.sh
|   |   `-- health_check.sh
|   `-- generate_logs.py
|-- tests/
|-- .github/workflows/main.yml
|-- DEPLOYMENT.md
|-- Dockerfile
|-- docker-compose.yml
|-- docker-compose.prod.yml
|-- requirements.txt
|-- run.py
`-- README.md
```

## API Usage

Start the API locally:

```bash
python -m pip install -r requirements.txt
python run.py
```

Health check:

```bash
curl http://localhost:5000/health
```

Ingest a log:

```bash
curl -X POST http://localhost:5000/logs \
  -H "Content-Type: application/json" \
  -d '{
    "service": "checkout-api",
    "level": "ERROR",
    "message": "ERROR payment provider timeout",
    "source": "demo",
    "trace_id": "abc-123",
    "metadata": {"region": "us-east-1"}
  }'
```

List logs:

```bash
curl http://localhost:5000/logs
```

List alerts:

```bash
curl http://localhost:5000/alerts
```

Generate simulated logs:

```bash
python scripts/generate_logs.py --count 30 --mode mixed
```

Generate logs through the API:

```bash
curl -X POST http://localhost:5000/logs/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 20, "mode": "anomaly"}'
```

## Detection Workflow

1. A service sends a log event to `POST /logs`.
2. The log processor validates fields, adds a timestamp, and creates a fingerprint.
3. The log is stored in SQLite.
4. The anomaly detector checks direct keywords, repeated failures, and high-frequency service events.
5. The alert handler stores matching alerts and sends notifications if configured.
6. Dashboard endpoints expose summaries for logs, services, and alerts.

## Environment Variables

Copy `.env.example` to `.env` for local customization:

```bash
cp .env.example .env
```

Important variables:

- `DATABASE_PATH`: SQLite database location
- `ERROR_KEYWORDS`: comma-separated detection keywords
- `REPEATED_FAILURE_THRESHOLD`: number of repeated failures before alerting
- `REPEATED_FAILURE_WINDOW_SECONDS`: repeated failure detection window
- `HIGH_FREQUENCY_THRESHOLD`: event count that triggers high-frequency detection
- `HIGH_FREQUENCY_WINDOW_SECONDS`: high-frequency detection window
- `ALERT_COOLDOWN_SECONDS`: suppresses duplicate alerts for the same rule and service
- `SLACK_WEBHOOK_URL`: optional Slack webhook for alert delivery
- `ALERT_EMAIL_ENABLED`: enables SMTP email alerting

## Docker Usage

Build and run with Docker:

```bash
docker build -t cloud-log-monitoring .
docker run -p 5000:5000 --env-file .env.example cloud-log-monitoring
```

Run locally with Docker Compose:

```bash
docker compose up --build
```

Run the EC2-style production Compose file:

```bash
cp .env.example .env
docker compose -f docker-compose.prod.yml up -d --build
curl http://localhost/health
```

`docker-compose.prod.yml` maps host port `80` to the container and stores SQLite data in a Docker volume.

## CI/CD Pipeline

The GitHub Actions workflow in `.github/workflows/main.yml` performs a practical deployment validation:

1. Checks out the repository
2. Installs Python dependencies
3. Runs the test suite with `python -m pytest tests -q`
4. Builds the Docker image
5. Starts the container and verifies `/health`

This mirrors the core DevOps flow used in many teams: test first, build an immutable artifact, then validate the runtime container.

## AWS EC2 Deployment

This repository includes a production-oriented EC2 deployment path:

- `docker-compose.prod.yml` maps host port `80` to the Flask/Gunicorn container.
- `scripts/ec2/bootstrap_ubuntu.sh` installs Docker and starts the app on first boot.
- `scripts/ec2/deploy.sh` pulls updates and restarts the production container.
- `DEPLOYMENT.md` provides the complete step-by-step EC2 guide.

Quick manual deployment:

1. Launch an Ubuntu EC2 instance.
2. Open inbound security group port `22` from your IP and port `80` for HTTP access.
3. SSH into the instance:

```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

4. Clone the repository and run the bootstrap script:

```bash
git clone https://github.com/AbhinavTupe/AI-Powered-Cloud-Log-Monitoring-Auto-Alert-System.git
cd AI-Powered-Cloud-Log-Monitoring-Auto-Alert-System
sudo bash scripts/ec2/bootstrap_ubuntu.sh
```

5. Validate the deployment:

```bash
curl http://localhost/health
```

From your browser:

```text
http://<EC2_PUBLIC_IP>/health
http://<EC2_PUBLIC_IP>/dashboard
```

For automated launch, paste the user data script from [DEPLOYMENT.md](DEPLOYMENT.md) into the EC2 launch wizard.

## Testing

Run tests locally:

```bash
python -m pytest tests -q
```

The tests cover health checks, log ingestion, keyword alerting, repeated failures, high-frequency detection, and alert summaries.

## Screenshot Placeholders

Add screenshots to a future `docs/screenshots/` folder:

- `docs/screenshots/health-check.png`
- `docs/screenshots/log-ingestion.png`
- `docs/screenshots/alerts-summary.png`
- `docs/screenshots/github-actions-ci.png`
- `docs/screenshots/ec2-deployment.png`

## Interview Talking Points

- The app uses a modular Flask structure similar to larger production services.
- SQLite keeps the project lightweight, but the database layer can be replaced with PostgreSQL.
- Detection rules are intentionally explainable, which is valuable for operations teams.
- Docker makes the app portable between local development, CI, and EC2.
- GitHub Actions validates code quality and deployability by building and running the container.
- EC2 deployment uses a simple VM plus Docker Compose model that is realistic for an internship demo.
- Environment variables keep deployment settings out of source code.

## Future Improvements

- Add authentication for API endpoints
- Add PostgreSQL support for higher-volume deployments
- Add a small HTML dashboard or React frontend
- Export Prometheus metrics
- Add severity-based Slack channels
- Add alert deduplication by fingerprint
- Add log retention policies
- Deploy behind Nginx with HTTPS

