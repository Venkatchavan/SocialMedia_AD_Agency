"""Authentication & RBAC — JWT tokens, roles, password hashing.

Roles: owner | admin | editor | viewer
Per-workspace role binding with JWT access + refresh tokens.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Role(str, Enum):
    """User roles ordered by privilege level."""

    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


# Privilege hierarchy: higher index = more privilege
_ROLE_HIERARCHY: dict[Role, int] = {
    Role.VIEWER: 0,
    Role.EDITOR: 1,
    Role.ADMIN: 2,
    Role.OWNER: 3,
}


@dataclass(frozen=True)
class TokenPayload:
    """Decoded JWT-like token payload."""

    user_id: str
    workspace_id: str
    role: Role
    exp: float
    iat: float
    token_type: str = "access"  # access | refresh


@dataclass
class WorkspaceBinding:
    """Maps a user to a role within a workspace."""

    user_id: str
    workspace_id: str
    role: Role


@dataclass
class UserRecord:
    """Minimal user record for auth checks."""

    user_id: str
    email: str
    password_hash: str
    bindings: list[WorkspaceBinding] = field(default_factory=list)


class PasswordHasher:
    """HMAC-SHA256 password hashing (no bcrypt dependency needed for core)."""

    def __init__(self, secret_key: str = "default-secret-change-me") -> None:
        self._secret = secret_key.encode()

    def hash_password(self, password: str) -> str:
        """Hash a password using HMAC-SHA256."""
        return hmac.new(
            self._secret,
            password.encode(),
            hashlib.sha256,
        ).hexdigest()

    def verify_password(self, password: str, hashed: str) -> bool:
        """Constant-time comparison of password against hash."""
        candidate = self.hash_password(password)
        return hmac.compare_digest(candidate, hashed)


class TokenManager:
    """Create and verify JWT-like tokens (HMAC-SHA256 signed JSON)."""

    def __init__(
        self,
        secret_key: str = "default-jwt-secret-change-me",
        access_ttl: int = 3600,
        refresh_ttl: int = 86400 * 7,
    ) -> None:
        self._secret = secret_key.encode()
        self._access_ttl = access_ttl
        self._refresh_ttl = refresh_ttl

    def create_access_token(
        self,
        user_id: str,
        workspace_id: str,
        role: Role,
    ) -> str:
        """Create a signed access token."""
        return self._create_token(
            user_id=user_id,
            workspace_id=workspace_id,
            role=role,
            token_type="access",
            ttl=self._access_ttl,
        )

    def create_refresh_token(
        self,
        user_id: str,
        workspace_id: str,
        role: Role,
    ) -> str:
        """Create a signed refresh token."""
        return self._create_token(
            user_id=user_id,
            workspace_id=workspace_id,
            role=role,
            token_type="refresh",
            ttl=self._refresh_ttl,
        )

    def verify_token(self, token: str) -> TokenPayload | None:
        """Verify and decode a token. Returns None if invalid/expired."""
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            return None

        payload_b64, signature = parts
        expected_sig = self._sign(payload_b64)
        if not hmac.compare_digest(signature, expected_sig):
            return None

        try:
            payload_json = json.loads(payload_b64)
        except (json.JSONDecodeError, ValueError):
            return None

        if payload_json.get("exp", 0) < time.time():
            return None

        return TokenPayload(
            user_id=payload_json["user_id"],
            workspace_id=payload_json["workspace_id"],
            role=Role(payload_json["role"]),
            exp=payload_json["exp"],
            iat=payload_json["iat"],
            token_type=payload_json.get("token_type", "access"),
        )

    def _create_token(
        self,
        user_id: str,
        workspace_id: str,
        role: Role,
        token_type: str,
        ttl: int,
    ) -> str:
        now = time.time()
        payload = {
            "user_id": user_id,
            "workspace_id": workspace_id,
            "role": role.value,
            "token_type": token_type,
            "iat": now,
            "exp": now + ttl,
        }
        payload_str = json.dumps(payload, separators=(",", ":"))
        signature = self._sign(payload_str)
        return f"{payload_str}.{signature}"

    def _sign(self, data: str) -> str:
        return hmac.new(
            self._secret,
            data.encode(),
            hashlib.sha256,
        ).hexdigest()


class AuthorizationError(Exception):
    """Raised when a user lacks required role."""

    def __init__(self, required: Role, actual: Role) -> None:
        self.required = required
        self.actual = actual
        super().__init__(
            f"Requires role '{required.value}', user has '{actual.value}'"
        )


def has_permission(user_role: Role, required_role: Role) -> bool:
    """Check if user_role meets or exceeds required_role."""
    return _ROLE_HIERARCHY[user_role] >= _ROLE_HIERARCHY[required_role]


def require_role(required: Role, user_role: Role) -> None:
    """Raise AuthorizationError if user_role is insufficient."""
    if not has_permission(user_role, required):
        raise AuthorizationError(required=required, actual=user_role)
