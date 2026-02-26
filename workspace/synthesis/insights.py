"""synthesis.insights — Generate insights markdown with asset_id references."""

from __future__ import annotations

from synthesis.clustering import Cluster
from core.schemas_asset import Asset
from core.logging import get_logger

_log = get_logger(__name__)


def generate_insights(
    clusters: list[Cluster],
    assets: list[Asset],
) -> str:
    """Produce insights.md content from clusters and assets."""
    asset_map = {a.asset_id: a for a in assets}
    lines: list[str] = ["# Creative Insights Report\n"]

    lines.append(f"\n**Total clusters:** {len(clusters)}\n")
    lines.append(f"**Total assets analysed:** {len(assets)}\n")

    for i, cl in enumerate(clusters, 1):
        lines.append(f"\n## Cluster {i}: {cl.cluster_key}\n")
        lines.append(f"- **Format:** {cl.format_type}\n")
        lines.append(f"- **Angle:** {cl.messaging_angle}\n")
        lines.append(f"- **Hook:** {cl.primary_hook}\n")
        lines.append(f"- **Offer:** {cl.offer_type}\n")
        lines.append(f"- **Count:** {cl.count}\n")
        lines.append("\n### Winner assets\n")
        for aid in cl.asset_ids[:5]:
            a = asset_map.get(aid)
            caption = (a.caption_or_copy or "")[:80] if a else ""
            lines.append(f"- `{aid}`: {caption}...\n")

    lines.append("\n---\n")
    lines.append("*Evidence-first: every insight references asset_id(s).*\n")
    md = "".join(lines)
    _log.info("Generated insights.md (%d chars)", len(md))
    return md
