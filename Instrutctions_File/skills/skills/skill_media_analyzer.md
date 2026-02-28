# skill_media_analyzer.md

## Purpose
Analyze creative media (video/image) and output deterministic tags.

## Inputs
- asset records with media_url/thumbnail_url
- taxonomy version
- max_video_seconds (cap first N seconds)

## Outputs
- tags.json (Tag JSON per asset)
- analysis_notes.json (optional short notes)

## Prompt (Vision Model)
Return ONLY JSON:
{
  "asset_id": "...",
  "asset_type": "video|image|carousel|unknown",
  "format_type": "...",
  "first_3_seconds": {
    "visual": "...",
    "spoken_hook": "...",
    "on_screen_text": "...",
    "pattern_interrupt": true
  },
  "hook_tactics": ["..."],
  "messaging_angle": ["..."],
  "offer": {"type":"...","terms":"...","urgency":"..."},
  "proof_elements": ["..."],
  "cta": {"type":"...","exact_text_if_visible":"..."},
  "objections_addressed": ["..."],
  "production_notes": {"pacing":"...","cuts_per_10s":"...","captions_style":"..."},
  "reuse_ideas": ["...","...","...","...","..."],
  "risk_flags": ["none"]
}

## Guardrails
- No competitor-copy generation.
- UNKNOWN if uncertain.
- Never output personal identifiers.

## Validation
- Ensure fields are from allowed enums
- Ensure JSON-only output