from flask import Blueprint, jsonify, request

from app.services.log_generator import generate_log_batch
from app.services.log_processor import LogProcessor

logs_bp = Blueprint("logs", __name__)


@logs_bp.get("/logs")
def list_logs():
    processor = LogProcessor()
    result = processor.list_logs(
        limit=request.args.get("limit", default=50, type=int),
        service=request.args.get("service"),
        level=request.args.get("level"),
    )
    return jsonify(result)


@logs_bp.post("/logs")
def ingest_log():
    payload = request.get_json(silent=True) or {}
    processor = LogProcessor()
    result = processor.ingest(payload)
    return jsonify(result), 201


@logs_bp.post("/logs/generate")
def generate_logs():
    payload = request.get_json(silent=True) or {}
    count = int(payload.get("count", 10))
    count = max(1, min(count, 100))
    processor = LogProcessor()

    generated = []
    for sample in generate_log_batch(count=count, mode=payload.get("mode", "mixed")):
        generated.append(processor.ingest(sample))

    return jsonify({"generated": len(generated), "results": generated}), 201

