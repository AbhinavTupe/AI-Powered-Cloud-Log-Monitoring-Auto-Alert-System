from flask import Blueprint, jsonify, request

from app.services.alert_handler import AlertHandler

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.get("/alerts")
def list_alerts():
    handler = AlertHandler()
    result = handler.list_alerts(
        limit=request.args.get("limit", default=50, type=int),
        status=request.args.get("status"),
        severity=request.args.get("severity"),
    )
    return jsonify(result)


@alerts_bp.patch("/alerts/<int:alert_id>/resolve")
def resolve_alert(alert_id):
    handler = AlertHandler()
    resolved = handler.resolve_alert(alert_id)
    status_code = 200 if resolved else 404
    return jsonify({"resolved": resolved, "alert_id": alert_id}), status_code

