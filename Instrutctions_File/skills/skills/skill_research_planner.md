# skill_research_planner.md

## Purpose
Define run scope and sampling strategy that stays bounded and evidence-first.

## Inputs
- workspace_id
- platforms: meta|tiktok
- date_range_days
- max_assets_per_brand
- competitors.yml
- budgets (time/cost)

## Outputs
- plan.json
- run_checklist.md

## Prompt Contract (Planner)
Return JSON only:
{
  "workspace_id": "...",
  "platforms": ["meta","tiktok"],
  "date_range_days": 30,
  "max_assets_per_brand": 30,
  "collection_plan": {
    "tiktok": {"keywords": [], "count_per_keyword": 10},
    "meta": {"ad_library_urls": []}
  },
  "analysis_budgets": {"max_video_seconds": 30, "max_tokens_stage": {}},
  "uncertainties": [],
  "next_actions": []
}

## Guardrails
- Never expand scope without explicit operator input.
- Prefer fewer assets with deeper analysis over huge scrapes.

## Validation
- Ensure plan respects max assets and budgets.
- Ensure all competitors have required URLs/keywords.