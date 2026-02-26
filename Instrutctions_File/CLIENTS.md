# CLIENTS.md

## Workspace Isolation
Each client workspace contains:
- BrandBible.md
- BriefTemplate.md
- CompliancePolicy.md
- Competitors.yml
- Runs folder with outputs

## Folder Convention
clients/<workspace_id>/
  BrandBible.md
  BriefTemplate.md
  CompliancePolicy.md
  Competitors.yml
  runs/YYYY-MM-DD/
    raw_refs.json
    assets.json
    tags.json
    insights.md
    brief.md
    qa_report.md
    aot_ledger.jsonl

## Competitors.yml (example)
```yaml
workspace_id: "ridge"
platforms: ["meta", "tiktok"]
date_range_days: 30
max_assets_per_brand: 30

competitors:
  - name: "CompetitorA"
    meta_ad_library_url: "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&view_all_page_id=..."
    tiktok_keywords: ["wallet", "minimal wallet", "card holder"]