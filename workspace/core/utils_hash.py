"""core.utils_hash — Deterministic hashing helpers."""

from __future__ import annotations

import hashlib


def hash_text(text: str | None) -> str | None:
    """SHA-256 of lowercased stripped text; None if input is None."""
    if text is None:
        return None
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()


def hash_bytes(data: bytes) -> str:
    """SHA-256 hex of raw bytes (for media dedup)."""
    return hashlib.sha256(data).hexdigest()


def stable_asset_id(platform: str, *parts: str) -> str:
    """Build a stable, prefixed asset ID.

    Examples
    -------
    >>> stable_asset_id("meta", "brand", "12345")
    'meta:brand:12345'
    """
    clean = [p.strip() for p in parts if p]
    return f"{platform}:" + ":".join(clean)
