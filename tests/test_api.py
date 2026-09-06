"""
Tests — API Endpoints

Verifies that the FastAPI application starts, serves health endpoints,
handles chat requests, and authenticates users.
"""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def auth_client(client):
    """Create an authenticated test client for the FastAPI app."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"} 
    )
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


class TestHealthEndpoints:
    """Test health and sovereignty endpoints."""

    def test_health_returns_200(self, client):
        """GET /health returns 200 with sovereignty info."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["sovereign"] is True
        assert data["external_access"] is False
        assert "models" in data
        assert "services" in data

    def test_health_contains_model_info(self, client):
        """Health endpoint lists all three model categories."""
        response = client.get("/health")
        data = response.json()
        models = data["models"]
        assert "reasoning" in models
        assert "coding" in models
        assert "vision" in models

    def test_health_contains_service_probes(self, client):
        """Health endpoint includes service connectivity probes."""
        response = client.get("/health")
        data = response.json()
        services = data["services"]
        assert "ollama" in services
        assert "qdrant" in services
        # Services may or may not be reachable — both states are valid
        assert services["ollama"]["status"] in ("reachable", "not_reachable")
        assert services["qdrant"]["status"] in ("reachable", "not_reachable")

    def test_sovereignty_returns_200(self, client):
        """GET /sovereignty returns zero-egress data."""
        response = client.get("/sovereignty")
        assert response.status_code == 200
        data = response.json()
        assert data["sovereign"] is True
        assert data["external_dns_queries"] == 0
        assert data["external_tcp_connections"] == 0
        assert data["cloud_ai_requests"] == 0
        assert data["bytes_uploaded_externally"] == 0


class TestSovereigntyHeaders:
    """Test that sovereignty headers are attached to every response."""

    def test_sovereignty_headers_present(self, client):
        """Every response includes sovereignty trace headers."""
        response = client.get("/health")
        assert response.headers.get("X-Sovereign") == "true"
        assert response.headers.get("X-External-Calls") == "0"
        assert "X-Request-ID" in response.headers
        assert "X-Duration-Ms" in response.headers


class TestChatEndpoint:
    """Test the main chat endpoint."""

    def test_chat_returns_valid_response(self, auth_client):
        """POST /api/v1/chat returns a valid ChatResponse."""
        response = auth_client.post(
            "/api/v1/chat",
            json={"message": "Hello, Sovereign AI"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "route" in data
        assert data["sovereign"] is True
        assert "request_id" in data
        assert "duration_ms" in data

    def test_chat_classifies_coding_task(self, auth_client):
        """Chat correctly classifies a coding request."""
        response = auth_client.post(
            "/api/v1/chat",
            json={"message": "Write Python code to calculate pump efficiency"},
        )
        data = response.json()
        route = data["route"]
        assert route["task_type"] == "coding"
        assert route["model"] == "qwen2.5-coder-7b"

    def test_chat_classifies_document_task(self, auth_client):
        """Chat correctly classifies a document reasoning request."""
        response = auth_client.post(
            "/api/v1/chat",
            json={"message": "Summarize this inspection report"},
        )
        data = response.json()
        route = data["route"]
        assert route["task_type"] == "document_reasoning"
        assert route["model"] == "qwen3-14b"

    def test_chat_rejects_empty_message(self, auth_client):
        """Chat rejects empty messages."""
        response = auth_client.post(
            "/api/v1/chat",
            json={"message": ""},
        )
        assert response.status_code == 422  # Validation error


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_valid_credentials(self, client):
        """Login with valid credentials returns JWT token."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"

    def test_login_invalid_credentials(self, client):
        """Login with wrong password returns 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_login_unknown_user(self, client):
        """Login with unknown username returns 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "test"},
        )
        assert response.status_code == 401

    def test_me_with_valid_token(self, client):
        """GET /auth/me with valid token returns user info."""
        # First, login to get a token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "engineer", "password": "eng123"},
        )
        token = login_response.json()["access_token"]

        # Then use the token
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "engineer"
        assert data["role"] == "engineering"

    def test_me_without_token(self, client):
        """GET /auth/me without token returns 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestAdminEndpoints:
    """Test admin endpoints."""

    def test_list_models(self, auth_client):
        """GET /admin/models lists all available models."""
        response = auth_client.get("/api/v1/admin/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) >= 5  # reasoning, coding, vision, embedding, reranker
        assert "gpu_vram_total_mb" in data

    def test_admin_health(self, auth_client):
        """GET /admin/health returns subsystem statuses."""
        response = auth_client.get("/api/v1/admin/health")
        assert response.status_code == 200
        data = response.json()
        assert data["api"] == "ok"
        assert data["sovereignty"] == "enforced"
        assert "ollama" in data
        assert "qdrant" in data


class TestNotFound:
    """Test 404 handling."""

    def test_unknown_path_returns_404(self, client):
        """Unknown paths return structured 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data["sovereign"] is True
