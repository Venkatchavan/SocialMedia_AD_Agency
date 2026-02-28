"""Storage Tools — CrewAI tool wrappers for media/asset storage."""

from __future__ import annotations

from typing import Any


class UploadAssetTool:
    """CrewAI-compatible tool for uploading media assets."""

    name: str = "upload_asset"
    description: str = (
        "Upload a media asset (image, video, audio) to secure object storage. "
        "Returns a signed, time-limited URL for the uploaded asset."
    )

    def __init__(self, storage_adapter: Any) -> None:
        self._storage = storage_adapter

    def run(
        self,
        file_path: str,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> dict:
        """Execute the tool — upload an asset."""
        return self._storage.upload(
            file_path=file_path,
            key=key,
            content_type=content_type,
        )


class GetSignedUrlTool:
    """CrewAI-compatible tool for getting signed media URLs."""

    name: str = "get_signed_url"
    description: str = (
        "Get a signed, time-limited download URL for a media asset. "
        "URLs expire after the specified hours (default 24h). "
        "All media URLs MUST be signed — never use permanent public URLs."
    )

    def __init__(self, storage_adapter: Any) -> None:
        self._storage = storage_adapter

    def run(self, key: str, expiry_hours: int = 24) -> dict:
        """Execute the tool — get a signed URL."""
        url = self._storage.download_url(key=key, expiry_hours=expiry_hours)
        return {
            "key": key,
            "signed_url": url,
            "expiry_hours": expiry_hours,
        }
