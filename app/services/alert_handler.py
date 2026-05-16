import json
import logging
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import requests
from flask import current_app

from app.database import get_db

logger = logging.getLogger(__name__)


class AlertHandler:
    """Persists alerts and optionally forwards them to Slack or email."""

    def create_alert(self, detection, log_record):
        if self._is_in_cooldown(detection.rule, log_record["service"]):
            logger.info("Alert suppressed by cooldown", extra={"rule": detection.rule})
            return None

        notification_status = self._notify(detection, log_record)
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO alerts (
                timestamp, severity, rule, service, message, log_id,
                status, notification_status, context_json
            )
            VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                detection.severity,
                detection.rule,
                log_record["service"],
                detection.message,
                log_record["id"],
                notification_status,
                json.dumps(detection.context),
            ),
        )
        db.commit()

        alert = self.get_alert(cursor.lastrowid)
        logger.warning("Alert created", extra={"alert_id": alert["id"], "rule": alert["rule"]})
        return alert

    def list_alerts(self, limit=50, status=None, severity=None):
        limit = max(1, min(limit or 50, 500))
        clauses = []
        params = []

        if status:
            clauses.append("status = ?")
            params.append(status)
        if severity:
            clauses.append("severity = ?")
            params.append(severity)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = get_db().execute(
            f"""
            SELECT *
            FROM alerts
            {where_sql}
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()

        alerts = [self._format_alert(row) for row in rows]
        return {"summary": self._summary(), "alerts": alerts}

    def resolve_alert(self, alert_id):
        db = get_db()
        cursor = db.execute("UPDATE alerts SET status = 'resolved' WHERE id = ?", (alert_id,))
        db.commit()
        return cursor.rowcount > 0

    def get_alert(self, alert_id):
        row = get_db().execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
        return self._format_alert(row) if row else None

    def _is_in_cooldown(self, rule, service):
        cooldown = current_app.config["ALERT_COOLDOWN_SECONDS"]
        if cooldown <= 0:
            return False

        since = (datetime.now(timezone.utc) - timedelta(seconds=cooldown)).isoformat()
        row = get_db().execute(
            """
            SELECT COUNT(*) AS count
            FROM alerts
            WHERE rule = ?
              AND service = ?
              AND timestamp >= ?
            """,
            (rule, service, since),
        ).fetchone()
        return row["count"] > 0

    def _notify(self, detection, log_record):
        channels = []

        slack_url = current_app.config["SLACK_WEBHOOK_URL"]
        if slack_url:
            channels.append(self._send_slack(slack_url, detection, log_record))

        if current_app.config["ALERT_EMAIL_ENABLED"]:
            channels.append(self._send_email(detection, log_record))

        if not channels:
            return "not_configured"

        if all(status == "sent" for status in channels):
            return "sent"
        return "partial_failure"

    def _send_slack(self, webhook_url, detection, log_record):
        payload = {
            "text": (
                f"[{detection.severity.upper()}] {detection.rule}: {detection.message} "
                f"service={log_record['service']} log_id={log_record['id']}"
            )
        }
        try:
            response = requests.post(webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            return "sent"
        except requests.RequestException as exc:
            logger.exception("Slack notification failed: %s", exc)
            return "failed"

    def _send_email(self, detection, log_record):
        required = [
            current_app.config["SMTP_HOST"],
            current_app.config["SMTP_USERNAME"],
            current_app.config["SMTP_PASSWORD"],
            current_app.config["ALERT_EMAIL_FROM"],
            current_app.config["ALERT_EMAIL_TO"],
        ]
        if not all(required):
            logger.warning("Email alerting is enabled but SMTP settings are incomplete")
            return "failed"

        message = EmailMessage()
        message["Subject"] = f"{detection.severity.upper()} alert: {detection.rule}"
        message["From"] = current_app.config["ALERT_EMAIL_FROM"]
        message["To"] = current_app.config["ALERT_EMAIL_TO"]
        message.set_content(
            f"{detection.message}\n\n"
            f"Service: {log_record['service']}\n"
            f"Log ID: {log_record['id']}\n"
            f"Original log: {log_record['message']}\n"
        )

        try:
            with smtplib.SMTP(current_app.config["SMTP_HOST"], current_app.config["SMTP_PORT"]) as smtp:
                smtp.starttls()
                smtp.login(current_app.config["SMTP_USERNAME"], current_app.config["SMTP_PASSWORD"])
                smtp.send_message(message)
            return "sent"
        except smtplib.SMTPException as exc:
            logger.exception("Email notification failed: %s", exc)
            return "failed"

    def _summary(self):
        rows = get_db().execute(
            """
            SELECT status, severity, COUNT(*) AS count
            FROM alerts
            GROUP BY status, severity
            """
        ).fetchall()

        summary = {"total": 0, "open": 0, "resolved": 0, "by_severity": {}}
        for row in rows:
            summary["total"] += row["count"]
            summary[row["status"]] = summary.get(row["status"], 0) + row["count"]
            summary["by_severity"][row["severity"]] = summary["by_severity"].get(row["severity"], 0) + row["count"]
        return summary

    def _format_alert(self, row):
        return {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "severity": row["severity"],
            "rule": row["rule"],
            "service": row["service"],
            "message": row["message"],
            "log_id": row["log_id"],
            "status": row["status"],
            "notification_status": row["notification_status"],
            "context": json.loads(row["context_json"] or "{}"),
        }

