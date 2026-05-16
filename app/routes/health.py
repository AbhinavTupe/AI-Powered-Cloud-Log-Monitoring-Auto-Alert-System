from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify

from app.database import get_db

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    get_db().execute("SELECT 1").fetchone()
    return jsonify(
        {
            "status": "healthy",
            "service": current_app.config["SERVICE_NAME"],
            "version": current_app.config["VERSION"],
            "database": "reachable",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

