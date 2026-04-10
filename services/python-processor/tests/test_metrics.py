from unittest.mock import patch
from fastapi.testclient import TestClient

import src.main as main_module
from src.main import app

client = TestClient(app)


def test_metrics_returns_200():
    response = client.get("/api/metrics")
    assert response.status_code == 200


def test_metrics_has_required_fields():
    data = client.get("/api/metrics").json()
    for field in [
        "total_requests_processed",
        "uptime_seconds",
        "uptime_human",
        "health_status",
        "started_at",
        "checked_at",
    ]:
        assert field in data, f"Missing field: {field}"


def test_metrics_types():
    data = client.get("/api/metrics").json()
    assert isinstance(data["total_requests_processed"], int)
    assert data["total_requests_processed"] >= 0
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0
    assert isinstance(data["uptime_human"], str)
    assert isinstance(data["health_status"], str)


def test_metrics_request_counter_increments():
    r1 = client.get("/api/metrics").json()
    r2 = client.get("/api/metrics").json()
    assert r2["total_requests_processed"] > r1["total_requests_processed"]


def test_metrics_health_unreachable_on_failure():
    with patch("src.main.httpx.get", side_effect=Exception("connection refused")):
        data = client.get("/api/metrics").json()
    assert data["health_status"] == "unreachable"
