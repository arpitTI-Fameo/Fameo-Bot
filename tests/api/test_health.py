"""
API tests for health and readiness endpoints.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """Create a test client with mocked database."""
    with patch("app.database.connection.init_database"):
        with patch("app.database.connection.close_database", new_callable=AsyncMock):
            app = create_app()
            with TestClient(app) as c:
                yield c


class TestHealthEndpoint:
    """Test GET /api/v1/health."""

    def test_health_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_has_request_id(self, client):
        response = client.get("/api/v1/health")
        assert "x-request-id" in response.headers

    def test_health_has_timing(self, client):
        response = client.get("/api/v1/health")
        assert "x-response-time-ms" in response.headers


class TestReadyEndpoint:
    """Test GET /api/v1/ready."""

    @patch(
        "app.api.v1.health.router.check_database_health",
        new_callable=AsyncMock,
        return_value=True,
    )
    def test_ready_all_healthy(self, mock_db, client):
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["database"] is True

    @patch(
        "app.api.v1.health.router.check_database_health",
        new_callable=AsyncMock,
        return_value=False,
    )
    def test_ready_database_down(self, mock_db, client):
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["database"] is False


class TestRequestMiddleware:
    """Test middleware behavior."""

    def test_custom_request_id_preserved(self, client):
        custom_id = "test-req-12345"
        response = client.get(
            "/api/v1/health",
            headers={"X-Request-ID": custom_id},
        )
        assert response.headers["x-request-id"] == custom_id

    def test_generated_request_id_format(self, client):
        response = client.get("/api/v1/health")
        request_id = response.headers["x-request-id"]
        # Should be a valid UUID
        assert len(request_id) == 36
        assert request_id.count("-") == 4
