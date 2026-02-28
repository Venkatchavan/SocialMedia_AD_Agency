"""Tests for LLM client service."""
from __future__ import annotations

import pytest

from app.services.llm_client import LLMClient


class TestLLMClientDryRun:
    """Test LLMClient in dry-run mode (default)."""

    def test_dry_run_default(self):
        """Client defaults to dry-run mode."""
        client = LLMClient(dry_run=True)
        assert client.is_dry_run is True

    def test_complete_returns_string(self):
        """complete() returns a string in dry-run mode."""
        client = LLMClient(dry_run=True)
        result = client.complete(
            system_prompt="You are helpful.",
            user_prompt="Hello",
            agent_id="scriptwriter",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_complete_json_returns_dict(self):
        """complete_json() returns a parsed dict in dry-run mode."""
        client = LLMClient(dry_run=True)
        result = client.complete_json(
            system_prompt="You are helpful.",
            user_prompt="Hello",
            agent_id="scriptwriter",
        )
        assert isinstance(result, dict)
        assert "hook" in result

    def test_dry_run_scriptwriter_response(self):
        """Scriptwriter dry-run response has expected structure."""
        client = LLMClient(dry_run=True)
        result = client.complete_json(
            system_prompt="test", user_prompt="test",
            agent_id="scriptwriter",
        )
        assert "hook" in result
        assert "scenes" in result
        assert "cta" in result

    def test_dry_run_caption_seo_response(self):
        """Caption SEO dry-run response has expected structure."""
        client = LLMClient(dry_run=True)
        result = client.complete_json(
            system_prompt="test", user_prompt="test",
            agent_id="caption_seo",
        )
        assert "caption" in result
        assert "hashtags" in result

    def test_dry_run_product_enrichment_response(self):
        """Product enrichment dry-run response has expected structure."""
        client = LLMClient(dry_run=True)
        result = client.complete_json(
            system_prompt="test", user_prompt="test",
            agent_id="product_enrichment",
        )
        assert "category_path" in result
        assert "primary_persona" in result
        assert "use_cases" in result

    def test_dry_run_manager_response(self):
        """Manager dry-run response has expected structure."""
        client = LLMClient(dry_run=True)
        result = client.complete_json(
            system_prompt="test", user_prompt="test",
            agent_id="manager",
        )
        assert "quality_score" in result
        assert "approved" in result

    def test_dry_run_unknown_agent(self):
        """Unknown agent_id returns generic dry-run response."""
        client = LLMClient(dry_run=True)
        result = client.complete_json(
            system_prompt="test", user_prompt="test",
            agent_id="unknown_agent",
        )
        assert isinstance(result, dict)
        assert "result" in result

    def test_parse_json_with_markdown_fences(self):
        """JSON parsing handles markdown code fences."""
        result = LLMClient._parse_json('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_plain(self):
        """JSON parsing handles plain JSON."""
        result = LLMClient._parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_invalid(self):
        """JSON parsing returns empty dict on failure."""
        result = LLMClient._parse_json("not json at all")
        assert result == {}

    def test_live_mode_requires_api_key(self):
        """Live mode raises ValueError without API key."""
        client = LLMClient(dry_run=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            client.complete(
                system_prompt="test",
                user_prompt="test",
            )
