# SCHEMA.md

## Asset JSON (minimum, v1.1 — backward compatible)
```json
{
  "asset_id": "meta:brand:ad:123",
  "platform": "meta|tiktok|x|pinterest",

  "workspace_id": "string",
  "run_id": "string",

  "brand": "string",
  "collected_at": "ISO8601",

  "ad_url": "string",
  "media_url": "string_or_null",
  "thumbnail_url": "string_or_null",

  "caption_or_copy": "string_or_null",
  "headline": "string_or_null",
  "cta": "string_or_null",

  "landing_page_url": "string_or_null",
  "landing_domain": "string_or_null",

  "first_seen_at": "ISO8601_or_null",
  "last_seen_at": "ISO8601_or_null",
  "status": "active|inactive|unknown",

  "text_hash": "string_or_null",
  "media_hash": "string_or_null",

  "metrics": {
    "impressions_range": "string_or_null",
    "views": "number_or_null",
    "likes": "number_or_null",
    "comments": "number_or_null",
    "shares": "number_or_null"
  },

  "metrics_extra": {
    "saves": "number_or_null",
    "reposts": "number_or_null",
    "clicks": "number_or_null"
  },

  "platform_fields": {
    "ad_id": "string_or_null",
    "post_id": "string_or_null",
    "page_id": "string_or_null",
    "pin_id": "string_or_null",
    "tweet_id": "string_or_null"
  },

  "provenance": {
    "collector": "string",
    "collector_version": "string_or_null",
    "source_url": "string_or_null",
    "fetched_at": "ISO8601",
    "http_status": "number_or_null",
    "notes": "string_or_null"
  }
}