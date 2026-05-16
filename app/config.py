import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _csv_env(name, default):
    raw_value = os.getenv(name, default)
    return [item.strip().upper() for item in raw_value.split(",") if item.strip()]


class Config:
    SERVICE_NAME = os.getenv("SERVICE_NAME", "ai-powered-cloud-log-monitor")
    VERSION = os.getenv("APP_VERSION", "1.0.0")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    DATABASE_PATH = os.getenv("DATABASE_PATH", str(Path("instance") / "monitoring.db"))

    ERROR_KEYWORDS = _csv_env("ERROR_KEYWORDS", "ERROR,FAILED,TIMEOUT")
    REPEATED_FAILURE_THRESHOLD = int(os.getenv("REPEATED_FAILURE_THRESHOLD", "3"))
    REPEATED_FAILURE_WINDOW_SECONDS = int(os.getenv("REPEATED_FAILURE_WINDOW_SECONDS", "300"))
    HIGH_FREQUENCY_THRESHOLD = int(os.getenv("HIGH_FREQUENCY_THRESHOLD", "20"))
    HIGH_FREQUENCY_WINDOW_SECONDS = int(os.getenv("HIGH_FREQUENCY_WINDOW_SECONDS", "60"))
    ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", "60"))

    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

    ALERT_EMAIL_ENABLED = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM", "")
    ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")

