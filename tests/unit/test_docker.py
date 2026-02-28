"""Tests for Docker configuration files (U-9)."""

from __future__ import annotations

from pathlib import Path



REPO_ROOT = Path(__file__).resolve().parents[2]


class TestDockerFiles:
    """Verify Docker configuration files exist and are well-formed."""

    def test_dockerfile_exists(self) -> None:
        assert (REPO_ROOT / "Dockerfile").is_file()

    def test_docker_compose_exists(self) -> None:
        assert (REPO_ROOT / "docker-compose.yml").is_file()

    def test_dockerignore_exists(self) -> None:
        assert (REPO_ROOT / ".dockerignore").is_file()

    def test_dockerfile_has_multistage(self) -> None:
        content = (REPO_ROOT / "Dockerfile").read_text()
        assert "AS builder" in content
        assert "AS runtime" in content

    def test_dockerfile_runs_as_nonroot(self) -> None:
        content = (REPO_ROOT / "Dockerfile").read_text()
        assert "USER agency" in content

    def test_dockerfile_has_healthcheck(self) -> None:
        content = (REPO_ROOT / "Dockerfile").read_text()
        assert "HEALTHCHECK" in content

    def test_compose_has_required_services(self) -> None:
        content = (REPO_ROOT / "docker-compose.yml").read_text()
        for service in ("db:", "redis:", "pipeline:", "api:"):
            assert service in content, f"Missing service: {service}"

    def test_compose_postgres_16(self) -> None:
        content = (REPO_ROOT / "docker-compose.yml").read_text()
        assert "postgres:16-alpine" in content

    def test_compose_redis_7(self) -> None:
        content = (REPO_ROOT / "docker-compose.yml").read_text()
        assert "redis:7-alpine" in content

    def test_compose_volumes_declared(self) -> None:
        content = (REPO_ROOT / "docker-compose.yml").read_text()
        assert "pgdata:" in content
        assert "redisdata:" in content

    def test_dockerignore_excludes_tests(self) -> None:
        content = (REPO_ROOT / ".dockerignore").read_text()
        assert "tests/" in content

    def test_dockerignore_excludes_env(self) -> None:
        content = (REPO_ROOT / ".dockerignore").read_text()
        assert ".env" in content
