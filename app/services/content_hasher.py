"""Content hashing service for dedup and tamper detection.

Security: SHA-256 hashing for all content assets.
No duplicate content hash may be published on the same platform.
"""

from __future__ import annotations

import hashlib

import structlog

logger = structlog.get_logger(__name__)


class ContentHasher:
    """SHA-256 content hashing for dedup and integrity verification."""

    @staticmethod
    def hash_bytes(content: bytes) -> str:
        """Compute SHA-256 hash of raw bytes."""
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def hash_text(text: str) -> str:
        """Compute SHA-256 hash of text content."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_file(file_path: str) -> str:
        """Compute SHA-256 hash of a file, reading in chunks for efficiency."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def verify_hash(content: bytes | str, expected_hash: str) -> bool:
        """Verify content matches expected hash. Used for tamper detection."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        actual = hashlib.sha256(content).hexdigest()
        matches = actual == expected_hash
        if not matches:
            logger.warning(
                "hash_mismatch",
                expected=expected_hash[:16] + "...",
                actual=actual[:16] + "...",
            )
        return matches
