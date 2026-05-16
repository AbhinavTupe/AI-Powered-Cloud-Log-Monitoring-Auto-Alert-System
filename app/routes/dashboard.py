from flask import Blueprint, jsonify

from app.services.summary import build_dashboard_summary

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
@dashboard_bp.get("/dashboard")
def dashboard_summary():
    return jsonify(build_dashboard_summary())

