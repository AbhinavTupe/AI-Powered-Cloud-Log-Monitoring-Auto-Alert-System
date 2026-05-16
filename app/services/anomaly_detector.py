from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

from flask import current_app

from app.database import get_db


@dataclass
class Detection:
    rule: str
    severity: str
    message: str
    context: dict

    def to_dict(self):
        return asdict(self)


class AnomalyDetector:
    """Small rule engine that keeps detection logic separate from API code."""

    def analyze(self, log_record):
        detections = []
        level = log_record["level"].upper()
        message = log_record["message"].upper()

        for keyword in current_app.config["ERROR_KEYWORDS"]:
            if level == keyword or keyword in message:
                detections.append(
                    Detection(
                        rule=f"{keyword}_KEYWORD",
                        severity="critical" if keyword in {"ERROR", "FAILED"} else "warning",
                        message=f"{keyword} pattern detected in {log_record['service']} log stream.",
                        context={"matched_keyword": keyword},
                    )
                )

        repeated = self._detect_repeated_failures(log_record)
        if repeated:
            detections.append(repeated)

        high_frequency = self._detect_high_frequency(log_record)
        if high_frequency:
            detections.append(high_frequency)

        return detections

    def _detect_repeated_failures(self, log_record):
        threshold = current_app.config["REPEATED_FAILURE_THRESHOLD"]
        window_seconds = current_app.config["REPEATED_FAILURE_WINDOW_SECONDS"]
        since = (datetime.now(timezone.utc) - timedelta(seconds=window_seconds)).isoformat()

        row = get_db().execute(
            """
            SELECT COUNT(*) AS count
            FROM logs
            WHERE service = ?
              AND fingerprint = ?
              AND timestamp >= ?
              AND (level = 'ERROR' OR UPPER(message) LIKE '%FAILED%' OR UPPER(message) LIKE '%TIMEOUT%')
            """,
            (log_record["service"], log_record["fingerprint"], since),
        ).fetchone()

        count = row["count"]
        if count >= threshold:
            return Detection(
                rule="REPEATED_FAILURES",
                severity="critical",
                message=f"Repeated failure pattern observed {count} times in {window_seconds} seconds.",
                context={
                    "count": count,
                    "threshold": threshold,
                    "window_seconds": window_seconds,
                    "fingerprint": log_record["fingerprint"],
                },
            )
        return None

    def _detect_high_frequency(self, log_record):
        threshold = current_app.config["HIGH_FREQUENCY_THRESHOLD"]
        window_seconds = current_app.config["HIGH_FREQUENCY_WINDOW_SECONDS"]
        since = (datetime.now(timezone.utc) - timedelta(seconds=window_seconds)).isoformat()

        row = get_db().execute(
            """
            SELECT COUNT(*) AS count
            FROM logs
            WHERE service = ?
              AND timestamp >= ?
            """,
            (log_record["service"], since),
        ).fetchone()

        count = row["count"]
        if count >= threshold:
            return Detection(
                rule="HIGH_FREQUENCY_EVENTS",
                severity="warning",
                message=f"High log volume detected for {log_record['service']}.",
                context={"count": count, "threshold": threshold, "window_seconds": window_seconds},
            )
        return None

