"""Tests for YouTube and LinkedIn collectors (U-6)."""

from __future__ import annotations

import os

import pytest

from app.collectors.base_collector import CollectedAd, BaseCollector
from app.collectors.youtube_collector import YouTubeCollector, _parse_datetime
from app.collectors.linkedin_collector import (
    LinkedInCollector,
    _extract_media_urls,
    _detect_media_type,
)


# ── CollectedAd ──────────────────────────────────────────────────────

class TestCollectedAd:
    def test_defaults(self):
        ad = CollectedAd(platform="test", post_id="1")
        assert ad.platform == "test"
        assert ad.media_type == "video"
        assert ad.engagement == {}
        assert ad.collected_at is not None

    def test_with_engagement(self):
        ad = CollectedAd(
            platform="youtube",
            post_id="abc",
            engagement={"views": 1000, "likes": 50},
        )
        assert ad.engagement["views"] == 1000


# ── YouTubeCollector ─────────────────────────────────────────────────

class TestYouTubeCollector:
    def test_no_key_returns_empty(self, monkeypatch):
        monkeypatch.setenv("YOUTUBE_API_KEY", "")
        collector = YouTubeCollector(api_key="")
        assert not collector.validate_credentials()
        assert collector.collect("test", "ws1") == []

    def test_with_key_validates(self):
        collector = YouTubeCollector(api_key="test_key_123")
        assert collector.validate_credentials()

    def test_platform_name(self):
        assert YouTubeCollector.platform_name == "youtube"

    def test_build_search_params(self):
        collector = YouTubeCollector(api_key="key123")
        params = collector._build_search_params("headphones", 10)
        assert params["q"] == "headphones"
        assert params["type"] == "video"
        assert params["videoDuration"] == "short"
        assert params["maxResults"] == 10
        assert params["key"] == "key123"

    def test_max_results_capped_at_50(self):
        collector = YouTubeCollector(api_key="key")
        params = collector._build_search_params("q", 200)
        assert params["maxResults"] == 50

    def test_parse_search_response(self):
        collector = YouTubeCollector(api_key="key")
        response = {
            "items": [
                {
                    "id": {"videoId": "abc123"},
                    "snippet": {
                        "title": "Best Headphones 2025",
                        "description": "Review",
                        "channelTitle": "TechReviewer",
                        "channelId": "UC_test",
                        "publishedAt": "2025-01-15T10:00:00Z",
                        "thumbnails": {"high": {"url": "https://img.youtube.com/abc.jpg"}},
                    },
                },
                {
                    "id": {"videoId": "def456"},
                    "snippet": {
                        "title": "Budget Audio",
                        "description": "Comparison",
                        "channelTitle": "AudioGuy",
                    },
                },
            ]
        }
        ads = collector.parse_search_response(response)
        assert len(ads) == 2
        assert ads[0].platform == "youtube"
        assert ads[0].post_id == "abc123"
        assert ads[0].title == "Best Headphones 2025"
        assert ads[0].author == "TechReviewer"
        assert ads[0].published_at is not None
        assert "youtube.com/shorts/abc123" in ads[0].url

    def test_parse_empty_response(self):
        collector = YouTubeCollector(api_key="key")
        ads = collector.parse_search_response({"items": []})
        assert ads == []

    def test_parse_skips_missing_video_id(self):
        collector = YouTubeCollector(api_key="key")
        response = {"items": [{"id": {}, "snippet": {"title": "No ID"}}]}
        ads = collector.parse_search_response(response)
        assert ads == []


class TestParseDatetime:
    def test_valid_iso(self):
        dt = _parse_datetime("2025-01-15T10:00:00Z")
        assert dt is not None
        assert dt.year == 2025

    def test_none_input(self):
        assert _parse_datetime(None) is None

    def test_invalid_string(self):
        assert _parse_datetime("not-a-date") is None


# ── LinkedInCollector ────────────────────────────────────────────────

class TestLinkedInCollector:
    def test_no_token_returns_empty(self, monkeypatch):
        monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "")
        collector = LinkedInCollector(access_token="")
        assert not collector.validate_credentials()
        assert collector.collect("test", "ws1") == []

    def test_with_token_validates(self):
        collector = LinkedInCollector(access_token="tok_123")
        assert collector.validate_credentials()

    def test_platform_name(self):
        assert LinkedInCollector.platform_name == "linkedin"

    def test_build_request_params(self):
        collector = LinkedInCollector(access_token="tok")
        params = collector._build_request_params("brand", 20)
        assert params["count"] == 20
        assert params["q"] == "search"

    def test_max_results_capped_at_100(self):
        collector = LinkedInCollector(access_token="tok")
        params = collector._build_request_params("q", 500)
        assert params["count"] == 100

    def test_parse_creatives_response(self):
        collector = LinkedInCollector(access_token="tok")
        response = {
            "elements": [
                {
                    "creative": {
                        "id": "cr_001",
                        "landingPage": "https://example.com",
                        "content": {
                            "textAd": {
                                "headline": "Try Our SaaS",
                                "body": "Best tool for teams",
                            },
                            "image": {"url": "https://img.linkedin.com/ad.png"},
                        },
                        "campaign": "camp_001",
                        "status": "ACTIVE",
                    },
                    "analytics": {
                        "impressions": 5000,
                        "clicks": 250,
                        "reactions": 100,
                    },
                }
            ]
        }
        ads = collector.parse_creatives_response(response)
        assert len(ads) == 1
        assert ads[0].platform == "linkedin"
        assert ads[0].title == "Try Our SaaS"
        assert ads[0].engagement["impressions"] == 5000
        assert ads[0].engagement["clicks"] == 250

    def test_parse_empty_response(self):
        collector = LinkedInCollector(access_token="tok")
        ads = collector.parse_creatives_response({"elements": []})
        assert ads == []


class TestHelpers:
    def test_extract_media_urls_image(self):
        urls = _extract_media_urls({"image": {"url": "https://img.com/a.png"}})
        assert urls == ["https://img.com/a.png"]

    def test_extract_media_urls_empty(self):
        assert _extract_media_urls({}) == []

    def test_detect_video(self):
        assert _detect_media_type({"video": {}}) == "video"

    def test_detect_image(self):
        assert _detect_media_type({"image": {}}) == "image"

    def test_detect_text(self):
        assert _detect_media_type({"textAd": {}}) == "text"
