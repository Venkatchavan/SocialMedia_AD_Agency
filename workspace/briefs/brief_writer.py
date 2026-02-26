"""briefs.brief_writer — Generate BriefObject from insights + brand bible."""

from __future__ import annotations

from core.config import USE_LLM_BRIEF
from core.logging import get_logger
from core.schemas_brief import (
    Audience,
    BriefObject,
    BriefTestVariant,
    CreativeDirection,
    Insight,
    Mandatories,
    Offer,
    RiskCompliance,
    Script,
    ScriptBeat,
)
from synthesis.clustering import Cluster

_log = get_logger(__name__)


def _llm_enrich(insights_md: str, brand_bible: str, clusters: list[Cluster]) -> dict:
    """Generate SMP, background, and RTBs via Gemini (primary) or OpenAI (fallback)."""
    cluster_summary = "; ".join(
        f"{c.primary_hook} x {c.messaging_angle} ({c.count} ads)" for c in clusters[:4]
    )
    prompt = (
        "You are a senior performance creative strategist.\n"
        f"Winning ad clusters: {cluster_summary}\n"
        f"Brand context: {brand_bible[:300]}\n"
        f"Insights: {insights_md[:600]}\n\n"
        "Return EXACTLY this format (no markdown):\n"
        "SMP: <one sentence single-minded proposition>\n"
        "BACKGROUND: <2 sentence brief background>\n"
        "RTB1: <reason to believe 1>\n"
        "RTB2: <reason to believe 2>\n"
        "RTB3: <reason to believe 3>"
    )

    raw = _call_gemini(prompt) or _call_openai(prompt)
    if not raw:
        return {}
    result: dict = {}
    for line in raw.strip().splitlines():
        if ": " in line:
            key, _, val = line.partition(": ")
            result[key.strip()] = val.strip()
    _log.info("LLM brief enrichment OK")
    return result


def _call_gemini(prompt: str) -> str | None:
    try:
        from analyzers.gemini_client import GeminiClient
        client = GeminiClient()
        if not client.is_available():
            return None
        return client.generate_text(prompt, max_tokens=300)
    except Exception as exc:
        _log.warning("Gemini enrichment failed: %s", exc)
        return None


def _call_openai(prompt: str) -> str | None:
    try:
        from core.config import OPENAI_API_KEY
        if not OPENAI_API_KEY:
            return None
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4,
        )
        return resp.choices[0].message.content
    except Exception as exc:
        _log.warning("OpenAI enrichment failed: %s", exc)
        return None


def write_brief(
    workspace_id: str,
    run_id: str,
    clusters: list[Cluster],
    insights_md: str,
    brand_bible: str,
) -> BriefObject:
    """Build a BriefObject deterministically from synthesis outputs."""
    llm_data: dict = {}
    if USE_LLM_BRIEF:
        llm_data = _llm_enrich(insights_md, brand_bible, clusters)

    top_clusters = clusters[:4]
    all_asset_ids = []
    for c in clusters:
        all_asset_ids.extend(c.asset_ids[:3])

    directions = [_direction_from_cluster(c) for c in top_clusters]
    hooks = _generate_hooks(top_clusters)
    scripts = _generate_scripts(top_clusters)
    matrix = _generate_matrix(top_clusters)

    brief = BriefObject(
        workspace_id=workspace_id,
        run_id=run_id,
        background=llm_data.get("BACKGROUND") or _extract_background(brand_bible, insights_md),
        objective_primary="Drive high-intent traffic via performance creative",
        objective_secondary="Build pattern library for scaling winners",
        audience=Audience(
            persona="Primary buyer persona from brand bible",
            situation="Active shopper evaluating alternatives",
            barriers=["Price sensitivity", "Trust / social proof"],
        ),
        insight=Insight(
            tension="Audience overwhelmed by options; craves social proof",
            why_now="Seasonal demand spike + competitive gap",
        ),
        smp=llm_data.get("SMP") or _derive_smp(top_clusters),
        rtbs=[llm_data[k] for k in ("RTB1", "RTB2", "RTB3") if k in llm_data] or _derive_rtbs(top_clusters),
        offer=Offer(type="percent_off", terms="20% off first order", urgency="Limited time"),
        mandatories=Mandatories(
            must_include=["Brand logo", "Legal disclaimer"],
            must_avoid=["Competitor names verbatim", "Unsubstantiated claims"],
            legal=["Results may vary", "See terms"],
        ),
        creative_directions=directions,
        hook_bank=hooks,
        scripts=scripts,
        testing_matrix=matrix,
        risks=RiskCompliance(
            claim_risks=["Avoid absolute efficacy claims"],
            platform_risks=["TikTok policy review for health adjacents"],
        ),
        evidence_assets=list(set(all_asset_ids)),
    )
    _log.info("Brief generated with %d directions, %d hooks", len(directions), len(hooks))
    return brief


def _extract_background(brand_bible: str, insights_md: str) -> str:
    snippet = brand_bible[:200] if brand_bible else "Brand context not loaded."
    return f"Based on brand bible and {len(insights_md)} chars of insights. {snippet}"


def _derive_smp(clusters: list[Cluster]) -> str:
    if not clusters:
        return "UNKNOWN — insufficient data"
    top = clusters[0]
    return f"The {top.messaging_angle} approach via {top.format_type} creative wins."


def _derive_rtbs(clusters: list[Cluster]) -> list[str]:
    rtbs: list[str] = []
    for c in clusters[:3]:
        rtbs.append(f"{c.count} top ads use {c.primary_hook} hook + {c.messaging_angle} angle")
    return rtbs or ["UNKNOWN — insufficient evidence"]


def _direction_from_cluster(c: Cluster) -> CreativeDirection:
    return CreativeDirection(
        angle=c.messaging_angle,
        hook=c.primary_hook,
        proof=c.format_type,
        cta="shop_now",
        notes=f"Based on cluster [{c.cluster_key}] with {c.count} assets",
    )


def _generate_hooks(clusters: list[Cluster]) -> list[str]:
    hooks: list[str] = []
    templates = [
        "Stop scrolling — this changes everything",
        "I tried every {angle} product. Here's the winner.",
        "POV: you finally found {angle} that works",
        "Nobody talks about this {hook} trick",
        "Watch what happens when you try {format}",
    ]
    for c in clusters:
        for t in templates[:3]:
            hooks.append(t.format(angle=c.messaging_angle, hook=c.primary_hook, format=c.format_type))
    return hooks[:20]


def _generate_scripts(clusters: list[Cluster]) -> list[Script]:
    scripts: list[Script] = []
    for c in clusters[:3]:
        scripts.append(Script(
            title=f"Script: {c.primary_hook} × {c.messaging_angle}",
            beats=[
                ScriptBeat(time_range="0-3s", action=f"Hook: {c.primary_hook}", on_screen_text="Bold claim", b_roll="Product close-up"),
                ScriptBeat(time_range="3-7s", action="Problem setup", on_screen_text="Pain point text", b_roll="Relatable scene"),
                ScriptBeat(time_range="7-15s", action=f"Proof: {c.format_type}", on_screen_text="Stats/demo", b_roll="Product in use"),
                ScriptBeat(time_range="15-25s", action="CTA + offer", on_screen_text="Shop Now + offer", b_roll="Logo + product"),
            ],
            cta_line="Shop Now — limited-time offer",
        ))
    return scripts


def _generate_matrix(clusters: list[Cluster]) -> list[BriefTestVariant]:
    variants: list[BriefTestVariant] = []
    for i, c in enumerate(clusters[:4]):
        variants.append(BriefTestVariant(
            variant=f"V{i+1}",
            hook=c.primary_hook,
            angle=c.messaging_angle,
            offer=c.offer_type,
            cta="shop_now",
            format=c.format_type,
        ))
    return variants
