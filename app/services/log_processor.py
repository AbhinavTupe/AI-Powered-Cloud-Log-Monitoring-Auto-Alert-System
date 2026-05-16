import json
import logging
import re
from datetime import datetime, timezone

from app.database import get_db
from app.services.alert_handler import AlertHandler
from app.services.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)

VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class LogProcessor:
    """Coordinates ingestion, persistence, detection, and alert creation."""

    def __init__(self):
        self.detector = AnomalyDetector()
        self.alert_handler = AlertHandler()

    def ingest(self, payload):
        log_record = self._normalize_payload(payload)
        saved_log = self._save_log(log_record)
        detections = self.detector.analyze(saved_log)

        alerts = []
        for detection in detections:
            alert = self.alert_handler.create_alert(detection, saved_log)
            if alert:
                alerts.append(alert)

        logger.info(
            "Log ingested",
            extra={"log_id": saved_log["id"], "service": saved_log["service"], "alert_count": len(alerts)},
        )
        return {
            "log": saved_log,
            "detections": [detection.to_dict() for detection in detections],
            "alerts_created": alerts,
        }

    def list_logs(self, limit=50, service=None, level=None):
        limit = max(1, min(limit or 50, 500))
        clauses = []
        params = []

        if service:
            clauses.append("service = ?")
            params.append(service)
        if level:
            clauses.append("level = ?")
            params.append(level.upper())

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = get_db().execute(
            f"""
            SELECT *
            FROM logs
            {where_sql}
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()

        return {"summary": self._summary(), "logs": [self._format_log(row) for row in rows]}

    def _normalize_payload(self, payload):
        message = str(payload.get("message", "")).strip()
        if not message:
            raise ValueError("Log payload requires a non-empty message")

        level = str(payload.get("level", "INFO")).upper()
        if level not in VALID_LEVELS:
            level = "INFO"

        service = str(payload.get("service", "sample-app")).strip() or "sample-app"
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": service,
            "level": level,
            "message": message,
            "source": str(payload.get("source", "api")).strip() or "api",
            "trace_id": payload.get("trace_id"),
            "fingerprint": self._fingerprint(message),
            "metadata": metadata,
        }

    def _save_log(self, log_record):
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO logs (
                timestamp, service, level, message, source, trace_id,
                fingerprint, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_record["timestamp"],
                log_record["service"],
                log_record["level"],
                log_record["message"],
                log_record["source"],
                log_record["trace_id"],
                log_record["fingerprint"],
                json.dumps(log_record["metadata"]),
            ),
        )
        db.commit()
        return self._format_log(get_db().execute("SELECT * FROM logs WHERE id = ?", (cursor.lastrowid,)).fetchone())

    def _summary(self):
        rows = get_db().execute(
            """
            SELECT level, COUNT(*) AS count
            FROM logs
            GROUP BY level
            """
        ).fetchall()

        total = sum(row["count"] for row in rows)
        return {"total": total, "by_level": {row["level"]: row["count"] for row in rows}}

    def _format_log(self, row):
        return {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "service": row["service"],
            "level": row["level"],
            "message": row["message"],
            "source": row["source"],
            "trace_id": row["trace_id"],
            "fingerprint": row["fingerprint"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    def _fingerprint(self, message):
        normalized = re.sub(r"\d+", "<num>", message.upper())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized[:160]

