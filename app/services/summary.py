from datetime import datetime, timedelta, timezone

from app.database import get_db


def build_dashboard_summary():
    db = get_db()
    now = datetime.now(timezone.utc)
    last_hour = (now - timedelta(hours=1)).isoformat()

    totals = db.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM logs) AS total_logs,
            (SELECT COUNT(*) FROM alerts) AS total_alerts,
            (SELECT COUNT(*) FROM alerts WHERE status = 'open') AS open_alerts,
            (SELECT COUNT(*) FROM logs WHERE timestamp >= ?) AS logs_last_hour
        """,
        (last_hour,),
    ).fetchone()

    top_services = db.execute(
        """
        SELECT service, COUNT(*) AS count
        FROM logs
        GROUP BY service
        ORDER BY count DESC
        LIMIT 5
        """
    ).fetchall()

    recent_alerts = db.execute(
        """
        SELECT id, timestamp, severity, rule, service, message, status
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT 5
        """
    ).fetchall()

    return {
        "summary": {
            "total_logs": totals["total_logs"],
            "total_alerts": totals["total_alerts"],
            "open_alerts": totals["open_alerts"],
            "logs_last_hour": totals["logs_last_hour"],
        },
        "top_services": [dict(row) for row in top_services],
        "recent_alerts": [dict(row) for row in recent_alerts],
    }

