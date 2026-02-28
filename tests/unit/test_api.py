"""Tests for FastAPI web layer (U-4)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Fresh FastAPI test client per test."""
    test_app = create_app()
    return TestClient(test_app)


# ── Health ─────────────────────────────────────────────


class TestHealth:
    def test_health_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ── Auth ───────────────────────────────────────────────


class TestAuthRoutes:
    def test_login_returns_tokens(self, client: TestClient) -> None:
        resp = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "secret",
            "workspace_id": "ws-1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_with_valid_token(self, client: TestClient) -> None:
        # First login
        login_resp = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "secret",
        })
        refresh = login_resp.json()["refresh_token"]

        # Then refresh
        resp = client.post("/api/auth/refresh", json={
            "refresh_token": refresh,
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_refresh_with_invalid_token(self, client: TestClient) -> None:
        resp = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid-token",
        })
        assert resp.status_code == 401

    def test_refresh_with_access_token_fails(self, client: TestClient) -> None:
        login_resp = client.post("/api/auth/login", json={
            "email": "x@x.com",
            "password": "y",
        })
        access = login_resp.json()["access_token"]

        resp = client.post("/api/auth/refresh", json={
            "refresh_token": access,
        })
        assert resp.status_code == 401


# ── Workspaces ─────────────────────────────────────────


class TestWorkspaceRoutes:
    def test_create_workspace(self, client: TestClient) -> None:
        resp = client.post("/api/workspaces/", json={
            "name": "Test Agency",
            "slug": "test-agency",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Agency"
        assert data["slug"] == "test-agency"
        assert data["is_active"] is True

    def test_get_workspace(self, client: TestClient) -> None:
        client.post("/api/workspaces/", json={
            "name": "WS", "slug": "ws-get",
        })
        resp = client.get("/api/workspaces/ws-get")
        assert resp.status_code == 200
        assert resp.json()["slug"] == "ws-get"

    def test_get_missing_workspace_404(self, client: TestClient) -> None:
        resp = client.get("/api/workspaces/nonexistent")
        assert resp.status_code == 404

    def test_list_workspaces(self, client: TestClient) -> None:
        resp = client.get("/api/workspaces/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ── Pipelines ─────────────────────────────────────────


class TestPipelineRoutes:
    def test_trigger_pipeline_returns_202(self, client: TestClient) -> None:
        resp = client.post("/api/pipelines/run", json={
            "asin": "B0XXXXXXXXX",
            "workspace_id": "ws-1",
            "platforms": ["tiktok"],
        })
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "queued"
        assert data["asin"] == "B0XXXXXXXXX"
        assert "run_id" in data

    def test_get_run_status(self, client: TestClient) -> None:
        # Trigger a run
        resp = client.post("/api/pipelines/run", json={
            "asin": "B0XXXXXXXXX",
        })
        run_id = resp.json()["run_id"]

        # Check status
        resp = client.get(f"/api/pipelines/{run_id}")
        assert resp.status_code == 200
        assert resp.json()["run_id"] == run_id

    def test_get_missing_run_404(self, client: TestClient) -> None:
        resp = client.get("/api/pipelines/nonexistent")
        assert resp.status_code == 404
