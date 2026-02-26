"""synthesis.aot_writer — Write Atom-of-Thought JSONL ledger."""

from __future__ import annotations

import json
from pathlib import Path

from core.enums import AoTType, Confidence
from core.schemas_aot import AoTAtom
from core.schemas_tag import TagSet
from synthesis.clustering import Cluster
from core.logging import get_logger

_log = get_logger(__name__)


def write_aot_ledger(
    clusters: list[Cluster],
    tags: list[TagSet],
    output_path: Path,
) -> list[AoTAtom]:
    """Generate EVIDENCE → TAG → HYPOTHESIS → DECISION → TEST atoms."""
    atoms: list[AoTAtom] = []

    # EVIDENCE atoms from tags
    for t in tags:
        atoms.append(
            AoTAtom(
                type=AoTType.EVIDENCE,
                source_assets=[t.asset_id],
                content=f"Asset tagged as {t.format_type.value}/{t.messaging_angle.value}.",
                confidence=Confidence.HIGH,
                next_check="Validate with vision model if available.",
            )
        )

    # TAG atoms per cluster
    for cl in clusters:
        atoms.append(
            AoTAtom(
                type=AoTType.TAG,
                source_assets=cl.asset_ids[:5],
                content=f"Cluster [{cl.cluster_key}] groups {cl.count} assets.",
                confidence=Confidence.MED,
                next_check="Review cluster purity.",
            )
        )

    # HYPOTHESIS for top clusters
    for cl in clusters[:3]:
        atoms.append(
            AoTAtom(
                type=AoTType.HYPOTHESIS,
                source_assets=cl.asset_ids[:3],
                content=(
                    f"Hypothesis: {cl.primary_hook}+{cl.messaging_angle} "
                    f"is a winning pattern in {cl.format_type} format."
                ),
                confidence=Confidence.MED,
                next_check="Validate via brief performance test.",
            )
        )

    # DECISION
    if clusters:
        top = clusters[0]
        atoms.append(
            AoTAtom(
                type=AoTType.DECISION,
                source_assets=top.asset_ids[:3],
                content=f"Lead with {top.cluster_key} pattern in next brief.",
                confidence=Confidence.MED,
                next_check="Monitor brief QA result.",
            )
        )

    # TEST
    if clusters:
        atoms.append(
            AoTAtom(
                type=AoTType.TEST,
                source_assets=[],
                content="A/B test top cluster pattern vs runner-up in next campaign cycle.",
                confidence=Confidence.LOW,
                next_check="Measure after 7 days of delivery.",
            )
        )

    # Write JSONL
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for atom in atoms:
            f.write(atom.model_dump_json() + "\n")
    _log.info("Wrote %d AoT atoms to %s", len(atoms), output_path)
    return atoms
