"""synthesis.clustering — Cluster assets by (format_type, messaging_angle, hook_tactics, offer_type)."""

from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel, Field

from core.schemas_tag import TagSet
from core.logging import get_logger

_log = get_logger(__name__)


class Cluster(BaseModel):
    cluster_key: str
    format_type: str
    messaging_angle: str
    primary_hook: str
    offer_type: str
    asset_ids: list[str] = Field(default_factory=list)
    count: int = 0


def cluster_tags(tags: list[TagSet]) -> list[Cluster]:
    """Group tags into clusters by composite key."""
    buckets: dict[str, list[str]] = defaultdict(list)
    tag_map: dict[str, TagSet] = {}

    for t in tags:
        key = _cluster_key(t)
        buckets[key].append(t.asset_id)
        tag_map[t.asset_id] = t

    clusters: list[Cluster] = []
    for key, ids in buckets.items():
        sample = tag_map[ids[0]]
        clusters.append(
            Cluster(
                cluster_key=key,
                format_type=sample.format_type.value,
                messaging_angle=sample.messaging_angle.value,
                primary_hook=sample.hook_tactics[0].value if sample.hook_tactics else "other",
                offer_type=sample.offer_type.value,
                asset_ids=ids,
                count=len(ids),
            )
        )
    clusters.sort(key=lambda c: c.count, reverse=True)
    _log.info("Formed %d clusters from %d tags", len(clusters), len(tags))
    return clusters


def _cluster_key(t: TagSet) -> str:
    hook = t.hook_tactics[0].value if t.hook_tactics else "other"
    return f"{t.format_type.value}|{t.messaging_angle.value}|{hook}|{t.offer_type.value}"
