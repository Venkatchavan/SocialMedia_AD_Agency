"""Secrets manager wrapper.

SECURITY (from Agents_Security.md):
- Agents NEVER print secrets.
- Agents NEVER store raw tokens in logs.
- All credentials come from secrets manager.
- Only approved agents can access publish credentials (RBAC enforced).
"""

from __future__ import annotations

import json
import os
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class SecretsManager:
    """Unified secrets access. Never hardcode or log credentials."""

    def __init__(self, backend: str = "env") -> None:
        self._backend = backend
        self._cache: dict[str, str] = {}
        logger.info("secrets_manager_initialized", backend=backend)

    def get_secret(self, key: str) -> str:
        """Fetch a secret by key. Cached per session.

        Args:
            key: The secret key (e.g., "OPENAI_API_KEY").

        Returns:
            The secret value.

        Raises:
            ValueError: If the secret is not found.
        """
        if key in self._cache:
            return self._cache[key]

        value: Optional[str] = None

        if self._backend == "env":
            value = os.environ.get(key, "")
        elif self._backend == "aws":
            value = self._get_from_aws(key)
        elif self._backend == "vault":
            value = self._get_from_vault(key)

        if not value:
            logger.error("secret_not_found", key=key, backend=self._backend)
            raise ValueError(f"Secret '{key}' not found in {self._backend}")

        self._cache[key] = value
        # NEVER log the secret value
        logger.info("secret_retrieved", key=key, backend=self._backend)
        return value

    def get_platform_credentials(self, platform: str) -> dict:
        """Get all credentials for a platform as a dict.

        Args:
            platform: Platform name (e.g., "tiktok", "instagram").

        Returns:
            Dict of credential key-value pairs.
        """
        prefix = platform.upper()
        if self._backend == "env":
            creds: dict[str, str] = {}
            for env_key, env_val in os.environ.items():
                if env_key.startswith(prefix) and env_val:
                    short_key = env_key[len(prefix) + 1:].lower()
                    creds[short_key] = env_val
            return creds
        elif self._backend == "aws":
            raw = self._get_from_aws(f"affiliate-agency/{platform}")
            return json.loads(raw) if raw else {}
        return {}

    def _get_from_aws(self, key: str) -> Optional[str]:
        """Fetch from AWS Secrets Manager."""
        try:
            import boto3

            client = boto3.client("secretsmanager")
            response = client.get_secret_value(SecretId=key)
            return response.get("SecretString", "")
        except Exception:
            logger.error("aws_secrets_error", key=key)
            return None

    def _get_from_vault(self, key: str) -> Optional[str]:
        """Fetch from HashiCorp Vault."""
        try:
            import hvac

            client = hvac.Client(url=os.environ.get("VAULT_ADDR", ""))
            client.token = os.environ.get("VAULT_TOKEN", "")
            secret = client.secrets.kv.v2.read_secret_version(path=key)
            return json.dumps(secret["data"]["data"])
        except Exception:
            logger.error("vault_secrets_error", key=key)
            return None

    def clear_cache(self) -> None:
        """Clear the in-memory cache. Used after credential rotation."""
        self._cache.clear()
        logger.info("secrets_cache_cleared")
