"""Unit tests for ContentHasher — SHA-256 hashing and dedup."""

from __future__ import annotations

from app.services.content_hasher import ContentHasher


class TestContentHasher:
    """Test suite for content hashing."""

    def test_hash_text_deterministic(self, content_hasher: ContentHasher):
        """Same text should always produce the same hash."""
        text = "This is a test caption #ad"
        hash1 = content_hasher.hash_text(text)
        hash2 = content_hasher.hash_text(text)
        assert hash1 == hash2

    def test_different_text_different_hash(self, content_hasher: ContentHasher):
        """Different text should produce different hashes."""
        hash1 = content_hasher.hash_text("Caption A")
        hash2 = content_hasher.hash_text("Caption B")
        assert hash1 != hash2

    def test_hash_is_hex_string(self, content_hasher: ContentHasher):
        """Hash should be a hex string."""
        h = content_hasher.hash_text("test")
        assert all(c in "0123456789abcdef" for c in h)

    def test_hash_length_sha256(self, content_hasher: ContentHasher):
        """SHA-256 hash should be 64 hex characters."""
        h = content_hasher.hash_text("test")
        assert len(h) == 64

    def test_verify_hash_correct(self, content_hasher: ContentHasher):
        """Verification should pass for correct text."""
        text = "original content"
        h = content_hasher.hash_text(text)
        assert content_hasher.verify_hash(text, h)

    def test_verify_hash_tampered(self, content_hasher: ContentHasher):
        """Verification should fail for modified text."""
        h = content_hasher.hash_text("original content")
        assert not content_hasher.verify_hash("tampered content", h)

    def test_empty_text_hashes(self, content_hasher: ContentHasher):
        """Empty text should still produce a valid hash."""
        h = content_hasher.hash_text("")
        assert len(h) == 64
