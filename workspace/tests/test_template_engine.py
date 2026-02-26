"""tests.test_template_engine — Validate brief template loading and rendering."""

from __future__ import annotations

import pytest

from core.schemas_brief import (
    Audience,
    BriefObject,
    CreativeDirection,
    Insight,
    Mandatories,
    Offer,
    RiskCompliance,
    Script,
    ScriptBeat,
    TestVariant,
)
from briefs.brief_renderer_md import render_brief_md


def _make_brief(**overrides) -> BriefObject:
    defaults = dict(
        workspace_id="test_ws",
        run_id="2026-01-01",
        background="Test background context.",
        objective_primary="Drive traffic",
        objective_secondary="Build pattern library",
        audience=Audience(
            persona="Test persona",
            situation="Active shopper",
            barriers=["Price", "Trust"],
        ),
        insight=Insight(tension="Too many options", why_now="Seasonal spike"),
        smp="The best product for fast results",
        rtbs=["RTB 1", "RTB 2", "RTB 3"],
        offer=Offer(type="percent_off", terms="20% off", urgency="Limited"),
        mandatories=Mandatories(
            must_include=["Logo"],
            must_avoid=["Competitor names"],
            legal=["Results may vary"],
        ),
        creative_directions=[
            CreativeDirection(
                angle="convenience",
                hook="curiosity_gap",
                proof="demo",
                cta="shop_now",
                notes="Test direction",
            )
        ],
        hook_bank=["Hook 1", "Hook 2", "Hook 3"],
        scripts=[
            Script(
                title="Script A",
                beats=[
                    ScriptBeat(
                        time_range="0-3s",
                        action="Hook",
                        on_screen_text="Bold text",
                        b_roll="Product",
                    )
                ],
                cta_line="Shop Now",
            )
        ],
        testing_matrix=[
            TestVariant(
                variant="V1",
                hook="curiosity_gap",
                angle="convenience",
                offer="percent_off",
                cta="shop_now",
                format="ugc_selfie",
            )
        ],
        risks=RiskCompliance(
            claim_risks=["No absolute claims"],
            platform_risks=["TikTok review"],
        ),
        evidence_assets=["tiktok:1", "meta:b:2"],
    )
    defaults.update(overrides)
    return BriefObject(**defaults)


class TestBriefRendering:
    def test_render_contains_smp(self):
        brief = _make_brief()
        md = render_brief_md(brief)
        assert "Single-Minded Proposition" in md
        assert "The best product for fast results" in md

    def test_render_contains_all_sections(self):
        brief = _make_brief()
        md = render_brief_md(brief)
        for section in [
            "Background", "Objective", "Audience", "Insight",
            "RTBs", "Offer", "Mandatories", "Creative Directions",
            "Hook Bank", "Scripts", "Testing Matrix", "Risks",
        ]:
            assert section in md, f"Missing section: {section}"

    def test_render_contains_evidence_count(self):
        brief = _make_brief()
        md = render_brief_md(brief)
        assert "2 referenced" in md

    def test_render_hooks_listed(self):
        brief = _make_brief()
        md = render_brief_md(brief)
        assert "Hook 1" in md
        assert "Hook 3" in md

    def test_render_empty_brief(self):
        brief = BriefObject(workspace_id="w", run_id="r")
        md = render_brief_md(brief)
        assert "Creative Brief" in md
