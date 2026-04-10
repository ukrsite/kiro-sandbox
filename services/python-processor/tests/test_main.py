"""
INTENTIONAL: Minimal test coverage -- only tests health endpoint.
Missing tests for process_users and generate_report.
"""
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "python-processor"
