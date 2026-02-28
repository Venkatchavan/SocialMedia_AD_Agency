"""analyzers.tagger_rules — Deterministic heuristic tagger (fallback when no vision key)."""

from __future__ import annotations

import re

from core.enums import (
    AssetType,
    CTAType,
    FormatType,
    HookTactic,
    MessagingAngle,
    OfferType,
    ProofElement,
    RiskFlag,
)
from core.schemas_asset import Asset
from core.schemas_tag import CTADetail, First3Seconds, OfferDetail, TagSet


def tag_asset_heuristic(asset: Asset) -> TagSet:
    """Apply rule-based heuristic tagging from caption/headline/CTA."""
    text = _combine_text(asset)
    return TagSet(
        asset_id=asset.asset_id,
        asset_type=_guess_asset_type(asset),
        format_type=_guess_format(text),
        hook_tactics=_guess_hooks(text),
        messaging_angle=_guess_angle(text),
        offer_type=_guess_offer(text),
        proof_elements=_guess_proof(text),
        cta_type=_guess_cta_type(asset.cta or ""),
        risk_flags=_detect_risks(text),
        first_3_seconds=First3Seconds(on_screen_text=asset.headline),
        offer=OfferDetail(type=_guess_offer(text)),
        cta=CTADetail(type=_guess_cta_type(asset.cta or "")),
    )


def _combine_text(a: Asset) -> str:
    parts = [a.caption_or_copy or "", a.headline or "", a.cta or ""]
    return " ".join(parts).lower()


def _guess_asset_type(a: Asset) -> AssetType:
    url = (a.media_url or "").lower()
    if any(ext in url for ext in (".mp4", ".mov", "video")):
        return AssetType.VIDEO
    if any(ext in url for ext in (".jpg", ".png", ".webp", "image")):
        return AssetType.IMAGE
    return AssetType.UNKNOWN


def _guess_format(text: str) -> FormatType:
    if re.search(r"(ugc|selfie|pov)", text):
        return FormatType.UGC_SELFIE
    if re.search(r"(demo|how.to|tutorial)", text):
        return FormatType.DEMO
    if re.search(r"(testimonial|review|customer)", text):
        return FormatType.TESTIMONIAL
    if re.search(r"(founder|ceo|creator)", text):
        return FormatType.FOUNDER
    return FormatType.UNKNOWN


def _guess_hooks(text: str) -> list[HookTactic]:
    hooks: list[HookTactic] = []
    if re.search(r"(stop|wait|hold on|you won't believe)", text):
        hooks.append(HookTactic.PATTERN_INTERRUPT)
    if re.search(r"(secret|finally|discover|the truth)", text):
        hooks.append(HookTactic.CURIOSITY_GAP)
    if re.search(r"(result|before.after|transformation)", text):
        hooks.append(HookTactic.RESULTS_FIRST)
    if re.search(r"(myth|wrong|lie|actually)", text):
        hooks.append(HookTactic.MYTH_BUST)
    if re.search(r"(problem|struggle|tired of|sick of)", text):
        hooks.append(HookTactic.PROBLEM_SOLUTION)
    return hooks or [HookTactic.OTHER]


def _guess_angle(text: str) -> MessagingAngle:
    if re.search(r"(pain|relief|sooth|heal)", text):
        return MessagingAngle.PAIN_RELIEF
    if re.search(r"(easy|quick|convenient|simple|fast)", text):
        return MessagingAngle.CONVENIENCE
    if re.search(r"(premium|luxury|exclusive|status)", text):
        return MessagingAngle.STATUS
    if re.search(r"(scien|clinical|study|research|proven)", text):
        return MessagingAngle.SCIENCE
    if re.search(r"(save|deal|value|affordable|cheap)", text):
        return MessagingAngle.VALUE
    return MessagingAngle.OTHER


def _guess_offer(text: str) -> OfferType:
    if re.search(r"\d+\s*%\s*off", text):
        return OfferType.PERCENT_OFF
    if re.search(r"bundle", text):
        return OfferType.BUNDLE
    if re.search(r"free\s*(gift|sample)", text):
        return OfferType.FREE_GIFT
    if re.search(r"(trial|free trial)", text):
        return OfferType.TRIAL
    if re.search(r"guarantee", text):
        return OfferType.GUARANTEE
    if re.search(r"subscribe.*save", text):
        return OfferType.SUBSCRIBE_SAVE
    return OfferType.UNKNOWN


def _guess_proof(text: str) -> list[ProofElement]:
    proofs: list[ProofElement] = []
    if re.search(r"(demo|watch|see how)", text):
        proofs.append(ProofElement.DEMO)
    if re.search(r"(\d+\s*(people|customers|reviews|stars))", text):
        proofs.append(ProofElement.SOCIAL_PROOF)
    if re.search(r"(doctor|expert|dermatologist|certified)", text):
        proofs.append(ProofElement.AUTHORITY)
    if re.search(r"(before.*after|transformation)", text):
        proofs.append(ProofElement.BEFORE_AFTER)
    return proofs or [ProofElement.NONE]


def _guess_cta_type(cta: str) -> CTAType:
    c = cta.lower()
    if "shop" in c or "buy" in c:
        return CTAType.SHOP_NOW
    if "learn" in c:
        return CTAType.LEARN_MORE
    if "subscribe" in c:
        return CTAType.SUBSCRIBE
    if "download" in c:
        return CTAType.DOWNLOAD
    return CTAType.UNKNOWN


def _detect_risks(text: str) -> list[RiskFlag]:
    flags: list[RiskFlag] = []
    if re.search(r"(cure|treat|heal|diagnos)", text):
        flags.append(RiskFlag.MEDICAL_CLAIM)
    if re.search(r"(invest|return|profit|guaranteed.*income)", text):
        flags.append(RiskFlag.FINANCIAL_CLAIM)
    return flags or [RiskFlag.NONE]
