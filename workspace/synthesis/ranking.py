"""synthesis.ranking — Rank assets by distribution proxy + recency."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from core.schemas_asset import Asset
from core.schemas_tag import TagSet
from core.logging import get_logger

_log = get_logger(__name__)


def rank_assets(
    assets: list[Asset],
    tags: list[TagSet] | None = None,
    *,
    top_n: int = 20,
) -> list[Asset]:
    """Return top-N assets sorted by composite score (desc)."""
    scored = [(a, _compute_score(a)) for a in assets]
    scored.sort(key=lambda x: x[1], reverse=True)
    ranked = [a for a, _ in scored[:top_n]]
    _log.info("Ranked %d → top %d assets", len(assets), len(ranked))
    return ranked


def _compute_score(asset: Asset) -> float:
    """Composite score: engagement proxy + recency bonus."""
    engagement = _engagement_score(asset)
    recency = _recency_score(asset)
    return engagement * 0.7 + recency * 0.3


def _engagement_score(asset: Asset) -> float:
    """Normalised engagement from available metrics."""
    m = asset.metrics
    total = (
        (m.views or 0) * 0.01
        + (m.likes or 0) * 1.0
        + (m.comments or 0) * 2.0
        + (m.shares or 0) * 3.0
    )
    # Simple log-scale normalisation
    import math
    return math.log1p(total)


def _recency_score(asset: Asset) -> float:
    """Score from 0..1 based on how recent the asset is (last 30 days = 1.0)."""
    ref_date = asset.last_seen_at or asset.first_seen_at or asset.collected_at
    try:
        dt = datetime.fromisoformat(ref_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - dt).days
        if age_days <= 0:
            return 1.0
        if age_days >= 90:
            return 0.0
        return max(0.0, 1.0 - age_days / 90.0)
    except Exception:
        return 0.5
