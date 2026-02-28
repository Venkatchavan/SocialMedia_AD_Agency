# AGENTS.md

## CrewAI Agents

### 1) Research Planner
- Defines scope, sampling, budgets, queries
- Output: plan.json + run checklist

### 2) TikTok Collector
- Approved scraping only
- Output: assets.json (public fields only)

### 3) Meta Collector
- Ad Library URL ingestion
- Output: assets.json (include impression range if available)

### 4) Media Analyzer (Vision)
- Output: tags.json (JSON only)

### 5) Comment Miner
- Output: comment_themes.json (anonymized)

### 6) Synthesizer (Strategist)
- Output: insights.md + clusters.json

### 7) Brief Writer
- Output: brief.md + brief.json

### 8) QA Gate
- Output: qa_report.md + qa_report.json
- Blocks export on FAIL

## Shared Output Envelope (All Agents)
{
  "status": "ok|warn|fail",
  "evidence_assets": ["asset_id..."],
  "output": {},
  "uncertainties": [],
  "next_actions": []
}

## Code Size Rule
All agent implementations: **no single code file > 250 lines.**