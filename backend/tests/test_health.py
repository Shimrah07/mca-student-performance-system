"""
Test for the health check endpoint.
Verifies that the FastAPI backend is running and responding to HTTP requests.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify that GET /health returns HTTP 200 and status 'ok'."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["message"] == "API is running"
    assert "environment" in data
