def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_ingest_info_log_without_alert(client):
    response = client.post(
        "/logs",
        json={"service": "checkout-api", "level": "INFO", "message": "Request completed successfully"},
    )

    payload = response.get_json()
    assert response.status_code == 201
    assert payload["log"]["service"] == "checkout-api"
    assert payload["alerts_created"] == []


def test_error_log_creates_alert(client):
    response = client.post(
        "/logs",
        json={"service": "payment-worker", "level": "ERROR", "message": "ERROR payment provider unavailable"},
    )

    payload = response.get_json()
    assert response.status_code == 201
    assert payload["detections"][0]["rule"] == "ERROR_KEYWORD"
    assert len(payload["alerts_created"]) >= 1


def test_repeated_failures_create_repeated_failure_detection(client):
    body = {"service": "auth-service", "level": "ERROR", "message": "ERROR login dependency failed for user 123"}
    client.post("/logs", json=body)
    response = client.post("/logs", json=body)

    rules = {item["rule"] for item in response.get_json()["detections"]}
    assert "REPEATED_FAILURES" in rules


def test_high_frequency_detection(client):
    body = {"service": "inventory-sync", "level": "INFO", "message": "Inventory sync heartbeat"}
    client.post("/logs", json=body)
    client.post("/logs", json=body)
    response = client.post("/logs", json=body)

    rules = {item["rule"] for item in response.get_json()["detections"]}
    assert "HIGH_FREQUENCY_EVENTS" in rules


def test_list_alerts_returns_summary(client):
    client.post(
        "/logs",
        json={"service": "checkout-api", "level": "ERROR", "message": "ERROR failed checkout operation"},
    )
    response = client.get("/alerts")

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["summary"]["total"] >= 1
    assert len(payload["alerts"]) >= 1

