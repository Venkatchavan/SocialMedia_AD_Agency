"""Storage Adapter — S3/MinIO object storage for media assets.

Uses boto3 (official AWS SDK). Supports S3, MinIO, and compatible services.
All URLs are signed and time-limited (Agents_Security.md).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog

from app.services.secrets import SecretsManager
from app.services.audit_logger import AuditLogger
from app.services.media_signer import MediaSigner

logger = structlog.get_logger(__name__)


class StorageAdapter:
    """S3/MinIO object storage adapter."""

    def __init__(
        self,
        secrets_manager: SecretsManager,
        audit_logger: AuditLogger,
        media_signer: MediaSigner | None = None,
        bucket_name: str = "ad-agency-assets",
    ) -> None:
        self._secrets = secrets_manager
        self._audit = audit_logger
        self._signer = media_signer
        self._bucket = bucket_name

    def upload(
        self,
        file_path: str,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> dict[str, str]:
        """Upload a file to object storage.

        TODO: Implement actual S3 upload using boto3.

        Returns:
            - key: str
            - bucket: str
            - signed_url: str (time-limited)
        """
        logger.info(
            "storage_upload",
            key=key,
            bucket=self._bucket,
            content_type=content_type,
        )

        self._audit.log(
            agent_id="storage_adapter",
            action="upload",
            decision="EXECUTED",
            reason=f"File uploaded to {self._bucket}/{key}",
            output_data={"key": key, "bucket": self._bucket},
        )

        # Generate signed URL
        signed_url = ""
        if self._signer:
            signed_url, _expiry = self._signer.generate_signed_url(
                storage_key=f"{self._bucket}/{key}",
            )

        return {
            "key": key,
            "bucket": self._bucket,
            "signed_url": signed_url,
        }

    def download_url(self, key: str, expiry_hours: int = 24) -> str:
        """Get a signed download URL for an asset.

        All media URLs MUST be signed and time-limited.
        """
        if not self._signer:
            raise RuntimeError("MediaSigner not configured — cannot generate signed URLs")

        url, _expiry = self._signer.generate_signed_url(
            storage_key=f"{self._bucket}/{key}",
            expiry_seconds=expiry_hours * 3600,
        )
        return url

    def delete(self, key: str) -> bool:
        """Delete an asset from storage.

        TODO: Implement actual S3 delete.
        """
        logger.info("storage_delete", key=key, bucket=self._bucket)

        self._audit.log(
            agent_id="storage_adapter",
            action="delete",
            decision="EXECUTED",
            reason=f"File deleted: {self._bucket}/{key}",
        )

        return True

    def list_assets(self, prefix: str = "") -> list[dict[str, Any]]:
        """List assets in a bucket prefix.

        TODO: Implement actual S3 listing.
        """
        logger.info("storage_list", prefix=prefix, bucket=self._bucket)
        return []
