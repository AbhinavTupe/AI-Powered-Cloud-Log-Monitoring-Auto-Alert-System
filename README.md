# AI-Powered Cloud Log Monitoring & Auto-Alert System

A production-style Flask monitoring platform that ingests application logs, detects abnormal patterns, stores events in SQLite, and triggers alerts through optional Slack or email integrations.

This project is designed for a Cloud/DevOps internship portfolio: it is modular, Dockerized, CI/CD ready, and explainable in an interview without requiring Kubernetes or a large cloud bill.

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

### Main Components

- `app/routes/` exposes REST endpoints for health checks, log ingestion, alert retrieval, and dashboard summaries.
- `app/services/log_processor.py` validates incoming log events and stores them.
- `app/services/anomaly_detector.py` detects `ERROR`, `FAILED`, `TIMEOUT`, repeated failures, and high-frequency events.
- `app/services/alert_handler.py` persists alerts and optionally sends Slack or email notifications.
- `app/services/log_generator.py` simulates real application logs for demos and testing.
- `app/database.py` initializes SQLite tables and indexes.

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
- AWS EC2 deployment-ready structure

## Project Structure

```text
.
├── app/
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── config.py
│   └── database.py
├── scripts/
│   └── generate_logs.py
├── tests/
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.py
└── README.md
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

You can also generate logs through the API:

```bash
curl -X POST http://localhost:5000/logs/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 20, "mode": "anomaly"}'
```

## Detection Workflow

1. A service sends a log event to `POST /logs`.
2. The log processor validates fields, adds a timestamp, and creates a fingerprint.
3. The log is stored in SQLite.
4. The anomaly detector checks:
   - direct `ERROR` matches
   - `FAILED` keyword matches
   - `TIMEOUT` keyword matches
   - repeated failure fingerprints within a time window
   - unusually high log frequency from one service
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

Run with Docker Compose:

```bash
docker compose up --build
```

Docker Compose mounts a named volume for SQLite data so alerts and logs survive container restarts.

## CI/CD Pipeline

The GitHub Actions workflow in `.github/workflows/ci.yml` performs a practical deployment validation:

1. Checks out the repository
2. Installs Python dependencies
3. Runs the test suite with `pytest`
4. Builds the Docker image
5. Starts the container and verifies `/health`

This mirrors the core DevOps flow used in many teams: test first, build an immutable artifact, then validate the runtime container.

## AWS EC2 Deployment Steps

1. Launch an Ubuntu EC2 instance.
2. Open inbound security group port `5000` for demo access, or port `80` if placing Nginx in front.
3. SSH into the instance:

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

4. Install Docker:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker ubuntu
```

5. Log out and back in, then clone the repository:

```bash
git clone https://github.com/<your-username>/ai-powered-cloud-log-monitoring.git
cd ai-powered-cloud-log-monitoring
```

6. Create a production environment file:

```bash
cp .env.example .env
```

7. Start the service:

```bash
docker compose up -d --build
```

8. Validate the deployment:

```bash
curl http://localhost:5000/health
```

For a more production-like setup, run this container behind Nginx and restrict direct access to port `5000`.

## Testing

Run tests locally:

```bash
pytest -q
```

The tests cover:

- health checks
- log ingestion
- keyword alerting
- repeated failure detection
- high-frequency detection
- alert listing and summary responses

## Screenshot Placeholders

Add screenshots to a future `docs/screenshots/` folder:

- `docs/screenshots/health-check.png`
- `docs/screenshots/log-ingestion.png`
- `docs/screenshots/alerts-summary.png`
- `docs/screenshots/github-actions-ci.png`
- `docs/screenshots/ec2-deployment.png`

## Interview Talking Points

- The app uses a modular Flask structure similar to larger production services.
- SQLite is used to keep the project lightweight, but the database layer can be replaced with PostgreSQL.
- Detection rules are intentionally explainable, which is valuable for operations teams.
- Docker makes the app portable between local development, CI, and EC2.
- GitHub Actions validates both code quality and deployability by building and running the container.
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

