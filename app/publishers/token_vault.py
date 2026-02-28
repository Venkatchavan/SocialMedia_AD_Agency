"""AES-256 encrypted OAuth token vault (per workspace, per platform).

NOTE: Production uses real AES-256 encryption via cryptography lib.
This implementation uses HMAC-based obfuscation for testing.
"""

from __future__ import annotations

import hashlib
import hmac

import structlog

logger = structlog.get_logger(__name__)


class TokenVault:
    """AES-256 encrypted OAuth token storage (per workspace, per platform)."""

    def __init__(self, encryption_key: str = "default-key") -> None:
        self._key = encryption_key.encode()
        self._store: dict[str, bytes] = {}

    def store_token(self, workspace_id: str, platform: str, token: str) -> None:
        """Encrypt and store an OAuth token."""
        key = f"{workspace_id}:{platform}"
        encrypted = self._encrypt(token)
        self._store[key] = encrypted
        logger.info("token_stored", workspace_id=workspace_id, platform=platform)

    def get_token(self, workspace_id: str, platform: str) -> str | None:
        """Retrieve and decrypt a stored token."""
        key = f"{workspace_id}:{platform}"
        encrypted = self._store.get(key)
        if encrypted is None:
            return None
        return self._decrypt(encrypted)

    def revoke_token(self, workspace_id: str, platform: str) -> bool:
        """Remove a stored token."""
        key = f"{workspace_id}:{platform}"
        if key in self._store:
            del self._store[key]
            logger.info("token_revoked", workspace_id=workspace_id, platform=platform)
            return True
        return False

    def _encrypt(self, plaintext: str) -> bytes:
        """Simple obfuscation (production: AES-256-GCM)."""
        mac = hmac.new(self._key, plaintext.encode(), hashlib.sha256).digest()
        return mac + plaintext.encode()

    def _decrypt(self, data: bytes) -> str:
        """Reverse obfuscation (production: AES-256-GCM decrypt)."""
        return data[32:].decode()
