# Tool Documentation

## Overview

The `app/tools/` package provides CrewAI-compatible tool wrappers that agents use to interact with adapters and services. Each tool follows the CrewAI `BaseTool` interface pattern with `name`, `description`, and `run()` method.

| Module | Tools | Purpose |
|--------|-------|---------|
| `amazon_tools.py` | `AmazonLookupTool`, `AmazonSearchTool` | Product data from Amazon PA-API |
| `content_tools.py` | `ContentHashTool`, `QACheckTool`, `DisclosureValidationTool` | Content hashing, QA, disclosure |
| `platform_tools.py` | `PlatformValidationTool` | Platform spec validation |
| `rights_tools.py` | `RightsCheckTool`, `RiskScoreTool` | Rights verification, risk scoring |
| `storage_tools.py` | `UploadAssetTool`, `GetSignedUrlTool` | Media upload and signed URLs |

---

## Amazon Tools

**Module:** `app/tools/amazon_tools.py`

### AmazonLookupTool

Look up an Amazon product by ASIN via official PA-API.

| Parameter | Type | Description |
|-----------|------|-------------|
| `asin` | `str` | Amazon Standard Identification Number |

**Returns:** Product dict with title, price, category, description, image URLs, and affiliate link.

### AmazonSearchTool

Search Amazon products by keywords.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keywords` | `str` | — | Search query |
| `category` | `str` | `""` | Category filter |
| `max_results` | `int` | `10` | Max products to return |

**Returns:** List of product dicts with title, price, and ASIN.

---

## Content Tools

**Module:** `app/tools/content_tools.py`

### ContentHashTool

Generate SHA-256 hash for content deduplication and tamper detection.

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | `str` | Content text to hash |

**Returns:** `{ content_hash, text_length }`

### QACheckTool

Run quality assurance checks before publishing. Checks compliance status, disclosures, duplicates, and content quality.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content_hash` | `str` | SHA-256 hash of content |
| `compliance_status` | `str` | Rights decision (APPROVED/REWRITE/REJECT) |
| `captions` | `dict[str, str]` | Platform → caption mapping |
| `target_platforms` | `list[str]` | Target platforms list |

**Returns:** `{ decision (APPROVE/REWRITE/REJECT), checks[], reason }`

### DisclosureValidationTool

Validate and auto-fix affiliate disclosure in captions per platform rules.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `caption` | `str` | — | Caption text |
| `platform` | `str` | — | Target platform |
| `auto_fix` | `bool` | `True` | Auto-add disclosure if missing |

**Returns:** `{ is_valid, reason, platform, fixed_caption?, auto_fixed? }`

---

## Platform Tools

**Module:** `app/tools/platform_tools.py`

### PlatformValidationTool

Validate media and caption content against platform specifications before publishing.

| Parameter | Type | Description |
|-----------|------|-------------|
| `platform` | `str` | Target platform name |
| `package` | `dict` | Content package with caption, media_info |

**Checks:**
- Caption length vs platform max
- Media format, duration, resolution, file size

**Returns:** `{ is_valid, platform, issues[], specs }`

---

## Rights Tools

**Module:** `app/tools/rights_tools.py`

### RightsCheckTool

Deterministic rights/licensing check for cultural references. No LLM involved.

| Parameter | Type | Description |
|-----------|------|-------------|
| `reference` | `dict` | Reference object with type, source, license info |

**Returns:** Rights decision dict (`{ decision, reason, reference_type }`)

### RiskScoreTool

Calculate a numerical risk score (0–100) for a reference.

| Parameter | Type | Description |
|-----------|------|-------------|
| `reference` | `dict` | Reference object |

**Returns:** `{ risk_score, action, auto_blocked, human_review_required }`

| Score Range | Action |
|-------------|--------|
| 0–39 | Auto-approve |
| 40–69 | Human review required |
| 70–100 | Auto-block |

---

## Storage Tools

**Module:** `app/tools/storage_tools.py`

### UploadAssetTool

Upload media assets to secure object storage. Returns a signed URL.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | `str` | — | Local file path |
| `key` | `str` | — | Storage key/path |
| `content_type` | `str` | `application/octet-stream` | MIME type |

**Returns:** Upload result with signed URL.

### GetSignedUrlTool

Generate a time-limited signed download URL for a media asset. Per security policy (Rule 6), all media URLs must be signed — permanent public URLs are never used.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `str` | — | Storage key |
| `expiry_hours` | `int` | `24` | URL expiry time |

**Returns:** `{ key, signed_url, expiry_hours }`
