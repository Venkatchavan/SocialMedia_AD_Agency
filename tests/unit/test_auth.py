"""Tests for Auth + RBAC (U-2)."""

from __future__ import annotations

import time

import pytest

from app.core.auth import (
    AuthorizationError,
    PasswordHasher,
    Role,
    TokenManager,
    TokenPayload,
    has_permission,
    require_role,
)


# ── Password Hashing ──────────────────────────────────


class TestPasswordHasher:
    """PasswordHasher hashes and verifies passwords."""

    def setup_method(self) -> None:
        self.hasher = PasswordHasher(secret_key="test-secret")

    def test_hash_returns_hex_string(self) -> None:
        h = self.hasher.hash_password("mypassword")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest

    def test_verify_correct_password(self) -> None:
        h = self.hasher.hash_password("secret123")
        assert self.hasher.verify_password("secret123", h) is True

    def test_verify_wrong_password(self) -> None:
        h = self.hasher.hash_password("secret123")
        assert self.hasher.verify_password("wrong", h) is False

    def test_different_secrets_produce_different_hashes(self) -> None:
        h1 = PasswordHasher("key-a").hash_password("pwd")
        h2 = PasswordHasher("key-b").hash_password("pwd")
        assert h1 != h2

    def test_same_password_same_hash(self) -> None:
        h1 = self.hasher.hash_password("abc")
        h2 = self.hasher.hash_password("abc")
        assert h1 == h2


# ── Token Manager ─────────────────────────────────────


class TestTokenManager:
    """TokenManager creates and verifies JWT-like tokens."""

    def setup_method(self) -> None:
        self.tm = TokenManager(
            secret_key="test-jwt-secret",
            access_ttl=3600,
            refresh_ttl=86400,
        )

    def test_create_and_verify_access_token(self) -> None:
        token = self.tm.create_access_token(
            user_id="user-1",
            workspace_id="ws-1",
            role=Role.EDITOR,
        )
        payload = self.tm.verify_token(token)
        assert payload is not None
        assert payload.user_id == "user-1"
        assert payload.workspace_id == "ws-1"
        assert payload.role == Role.EDITOR
        assert payload.token_type == "access"

    def test_create_and_verify_refresh_token(self) -> None:
        token = self.tm.create_refresh_token(
            user_id="user-2",
            workspace_id="ws-2",
            role=Role.OWNER,
        )
        payload = self.tm.verify_token(token)
        assert payload is not None
        assert payload.token_type == "refresh"
        assert payload.role == Role.OWNER

    def test_expired_token_returns_none(self) -> None:
        tm = TokenManager(secret_key="s", access_ttl=-1)
        token = tm.create_access_token("u", "w", Role.VIEWER)
        assert tm.verify_token(token) is None

    def test_tampered_token_returns_none(self) -> None:
        token = self.tm.create_access_token("u", "w", Role.VIEWER)
        tampered = token[:-5] + "XXXXX"
        assert self.tm.verify_token(tampered) is None

    def test_malformed_token_returns_none(self) -> None:
        assert self.tm.verify_token("not-a-token") is None
        assert self.tm.verify_token("") is None
        assert self.tm.verify_token("a.b.c.d") is None

    def test_wrong_secret_rejects(self) -> None:
        token = self.tm.create_access_token("u", "w", Role.VIEWER)
        other_tm = TokenManager(secret_key="different-secret")
        assert other_tm.verify_token(token) is None

    def test_token_contains_iat_and_exp(self) -> None:
        before = time.time()
        token = self.tm.create_access_token("u", "w", Role.VIEWER)
        payload = self.tm.verify_token(token)
        assert payload is not None
        assert payload.iat >= before
        assert payload.exp > payload.iat


# ── Role Hierarchy ─────────────────────────────────────


class TestRoleHierarchy:
    """has_permission() and require_role() enforce RBAC."""

    def test_owner_has_all_permissions(self) -> None:
        for role in Role:
            assert has_permission(Role.OWNER, role) is True

    def test_viewer_only_has_viewer(self) -> None:
        assert has_permission(Role.VIEWER, Role.VIEWER) is True
        assert has_permission(Role.VIEWER, Role.EDITOR) is False
        assert has_permission(Role.VIEWER, Role.ADMIN) is False
        assert has_permission(Role.VIEWER, Role.OWNER) is False

    def test_editor_has_editor_and_viewer(self) -> None:
        assert has_permission(Role.EDITOR, Role.VIEWER) is True
        assert has_permission(Role.EDITOR, Role.EDITOR) is True
        assert has_permission(Role.EDITOR, Role.ADMIN) is False

    def test_admin_has_admin_editor_viewer(self) -> None:
        assert has_permission(Role.ADMIN, Role.VIEWER) is True
        assert has_permission(Role.ADMIN, Role.EDITOR) is True
        assert has_permission(Role.ADMIN, Role.ADMIN) is True
        assert has_permission(Role.ADMIN, Role.OWNER) is False

    def test_require_role_passes(self) -> None:
        require_role(Role.EDITOR, Role.ADMIN)  # no exception

    def test_require_role_raises(self) -> None:
        with pytest.raises(AuthorizationError) as exc_info:
            require_role(Role.ADMIN, Role.VIEWER)
        assert exc_info.value.required == Role.ADMIN
        assert exc_info.value.actual == Role.VIEWER

    def test_require_role_exact_match(self) -> None:
        require_role(Role.EDITOR, Role.EDITOR)  # no exception
