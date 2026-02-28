# TOOLS.md

## Approved Tools Registry (Edit)
Collectors:
- Apify actors (authorized) for TikTok and Meta (if compliant in your org)
- Official APIs where applicable

Analyzers:
- Vision model (Gemini Vision or equivalent) for media understanding
- LLM for synthesis/brief writing

Storage:
- Postgres/SQLite/Supabase (structured)
- Store media pointers (thumb URLs) not raw videos

Export:
- Markdown / PDF / Notion / Google Docs (optional)

## Tool Use Rules (Hard)
- No CAPTCHA bypass, no auth bypass, no stealth automation.
- Respect rate limits and platform constraints.
- Never log secrets or raw tokens.
- Store minimal data:
  - asset IDs, timestamps, metrics/ranges, copy/caption (if public)
  - derived tags + anonymized comment themes
- Do not store usernames/handles or face crops.

## Code Size Rule
- **No single code file/module/script > 250 lines.**