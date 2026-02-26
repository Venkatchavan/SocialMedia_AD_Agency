"""analyzers.media_analyzer — Orchestrate vision tagging per asset."""

from __future__ import annotations

from core.config import USE_VISION_MODEL
from core.logging import get_logger
from core.schemas_asset import Asset
from core.schemas_tag import TagSet
from analyzers.gemini_client import GeminiClient
from analyzers.tagger_rules import tag_asset_heuristic

_log = get_logger(__name__)
_gemini = GeminiClient()

_VISION_PROMPT = (
    "Analyze this ad creative. Return JSON with: asset_type, format_type, "
    "hook_tactics, messaging_angle, offer_type, proof_elements, cta_type, "
    "risk_flags, first_3_seconds, offer, cta, objections_addressed, "
    "production_notes, reuse_ideas."
)


def analyze_asset(asset: Asset) -> TagSet:
    """Tag a single asset — vision model if available, else heuristic."""
    if USE_VISION_MODEL and _gemini.is_available():
        return _vision_tag(asset)
    return tag_asset_heuristic(asset)


def analyze_batch(assets: list[Asset]) -> list[TagSet]:
    """Tag a list of assets."""
    tags: list[TagSet] = []
    for a in assets:
        try:
            tags.append(analyze_asset(a))
        except Exception as exc:
            _log.warning("Analysis failed for %s: %s", a.asset_id, exc)
            tags.append(tag_asset_heuristic(a))
    _log.info("Analyzed %d / %d assets", len(tags), len(assets))
    return tags


def _vision_tag(asset: Asset) -> TagSet:
    """Attempt vision-model tagging; fall back on error."""
    url = asset.thumbnail_url or asset.media_url or ""
    if not url:
        return tag_asset_heuristic(asset)
    try:
        raw = _gemini.analyze_image(url, _VISION_PROMPT)
        return _parse_vision_response(raw, asset.asset_id)
    except Exception as exc:
        _log.warning("Vision fallback for %s: %s", asset.asset_id, exc)
        return tag_asset_heuristic(asset)


def _parse_vision_response(raw: dict, asset_id: str) -> TagSet:
    """Best-effort parse of vision model JSON into TagSet."""
    # Attempt to extract from typical Gemini response structure
    try:
        text_parts = raw.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        if text_parts:
            import json
            data = json.loads(text_parts[0].get("text", "{}"))
            data["asset_id"] = asset_id
            return TagSet.model_validate(data)
    except Exception:
        pass
    return TagSet(asset_id=asset_id)
