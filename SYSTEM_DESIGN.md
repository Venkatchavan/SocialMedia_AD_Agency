# CrewAI Affiliate Ad Agency — Complete System Design

> **Version**: 1.0.0  
> **Date**: 2026-02-25  
> **Author**: AI Systems Architect  
> **Status**: Production Blueprint  
> **Compliance**: All Agents.md rules enforced. All Agents_Security.md controls applied.

---

## SECTION 1 — SYSTEM OVERVIEW

### 1.1 Pipeline Summary

The system is an end-to-end AI-powered affiliate content pipeline for Amazon products. A solo founder operates the system; all labor-intensive steps are handled by CrewAI agents orchestrated through typed flows. The pipeline:

1. **Ingests** Amazon product candidates (via Product Advertising API or manual CSV).
2. **Enriches** products with category, audience persona, and use-case data.
3. **Maps** each product to culturally relevant references (movie/anime/music/novel).
4. **Validates** rights and licensing for every reference before creative use.
5. **Generates** scripts, visual prompts, images, videos, captions with affiliate disclosures.
6. **Adapts** content per platform (TikTok, Instagram, X, Pinterest).
7. **QA-checks** every asset against compliance, policy, and quality gates.
8. **Publishes** via official platform APIs (or queues for manual publish).
9. **Tracks** performance metrics and affiliate attribution.
10. **Experiments** with content angles and optimizes the loop.

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR / MANAGER AGENT                         │
│                     (CrewAI Flow Controller + State)                         │
└────────┬──────────┬──────────┬──────────┬──────────┬──────────┬─────────────┘
         │          │          │          │          │          │
    ┌────▼───┐ ┌────▼────┐ ┌──▼───┐ ┌───▼────┐ ┌──▼───┐ ┌───▼─────┐
    │PRODUCT │ │REFERENCE│ │RIGHTS│ │CREATIVE│ │ QA & │ │PUBLISH  │
    │ INTAKE │ │  INTEL  │ │ENGINE│ │ ENGINE │ │POLICY│ │  LAYER  │
    │ CREW   │ │  CREW   │ │(det.)│ │  CREW  │ │(det.)│ │  CREW   │
    └───┬────┘ └────┬────┘ └──┬───┘ └───┬────┘ └──┬───┘ └───┬─────┘
        │           │         │         │         │         │
   ┌────▼───────────▼─────────▼─────────▼─────────▼─────────▼──────┐
   │                     MESSAGE QUEUE (Redis / SQS)                │
   └────────────────────────────┬───────────────────────────────────┘
                                │
        ┌───────────────────────▼───────────────────────────┐
        │              SHARED DATA LAYER                     │
        │   PostgreSQL │ S3/MinIO │ Redis │ Audit Log Store  │
        └───────────────────────────────────────────────────┘
                                │
        ┌───────────────────────▼───────────────────────────┐
        │           ANALYTICS & EXPERIMENTATION              │
        │   Metrics Collector │ A/B Engine │ Optimizer        │
        └───────────────────────────────────────────────────┘
```

### 1.3 Agents vs Deterministic Services

| Component | Type | Reason |
|-----------|------|--------|
| Product Intake Agent | Agent | Flexible parsing, enrichment |
| Product Enrichment Agent | Agent | LLM-driven category/persona mapping |
| Reference Intelligence Agent | Agent | Creative cultural mapping requires LLM |
| Rights & License Verification | **Deterministic Service** | Compliance must NOT be opinion-based |
| Reference Risk Scoring | **Deterministic Service** | Scoring must be reproducible |
| Creative Strategy Agent | Agent | Creative decisions need LLM reasoning |
| Scriptwriter Agent | Agent | Content generation |
| Storyboard / Visual Prompt Agent | Agent | Creative visual direction |
| Asset Generation Coordinator | Agent + Service | Coordinates API calls to rendering |
| Video Assembly Agent | Service | Deterministic FFmpeg/rendering pipeline |
| Caption + SEO + Disclosure Agent | Agent | Language generation with rules |
| Platform Adaptation Agent | Agent | Platform-aware reformatting |
| QA & Policy Checker | **Deterministic Service** | Policy checks must be rule-based |
| Publisher / Scheduler | Service | API calls, scheduling, retry logic |
| Analytics & Experimentation | Service + Agent | Data collection deterministic; insights via LLM |
| Orchestrator / Manager | Agent (CrewAI Flow) | Flow control, state management |

### 1.4 Data Flow

```
Product Data ──► Enrichment ──► Reference Mapping ──► Rights Check
                                                          │
                                              ┌───────────┼───────────┐
                                              │           │           │
                                          APPROVE     REWRITE     REJECT
                                              │           │           │
                                              ▼           │           ▼
                                      Creative Gen ◄──────┘      Archive
                                              │
                                              ▼
                                      QA + Compliance
                                              │
                                    ┌─────────┼──────────┐
                                    │         │          │
                                APPROVE    REWRITE    REJECT
                                    │         │          │
                                    ▼         │          ▼
                               Publish ◄──────┘     Incident
                                    │
                                    ▼
                               Analytics ──► Experiment ──► Optimize ──► (loop)
```

---

## SECTION 2 — CREWAI ORCHESTRATION DESIGN

### 2.1 Crews

| Crew | Agents | Purpose |
|------|--------|---------|
| `ProductCrew` | Product Intake, Product Enrichment | Ingest and enrich product data |
| `ReferenceCrew` | Reference Intelligence, Rights Verification, Risk Scoring | Map references and validate rights |
| `CreativeCrew` | Creative Strategy, Scriptwriter, Storyboard, Asset Coordinator, Video Assembly, Caption+SEO | Generate all creative assets |
| `PublishCrew` | Platform Adaptation, QA & Policy, Publisher/Scheduler | Adapt, check, and publish |
| `AnalyticsCrew` | Analytics & Experimentation | Track, experiment, optimize |
| `OrchestratorCrew` | Orchestrator/Manager | Top-level flow control |

### 2.2 Flow Design (CrewAI Flows)

```python
from crewai.flow.flow import Flow, start, listen, router

class ContentPipelineFlow(Flow):
    # State tracks: product_id, reference_ids, compliance_status,
    # asset_ids, publish_status, experiment_id

    @start()
    def ingest_product(self):
        """Trigger: new product added or scheduled batch."""
        return ProductCrew.kickoff(inputs=self.state)

    @listen(ingest_product)
    def map_references(self):
        return ReferenceCrew.kickoff(inputs=self.state)

    @router(map_references)
    def rights_decision(self):
        if self.state.compliance_status == "APPROVED":
            return "generate"
        elif self.state.compliance_status == "REWRITE":
            return "rewrite_reference"
        else:
            return "reject"

    @listen("generate")
    def generate_content(self):
        return CreativeCrew.kickoff(inputs=self.state)

    @listen("rewrite_reference")
    def rewrite_and_remap(self):
        self.state.rewrite_count += 1
        if self.state.rewrite_count > 3:
            return self.reject()
        return self.map_references()

    @listen(generate_content)
    def qa_and_publish(self):
        return PublishCrew.kickoff(inputs=self.state)

    @router(qa_and_publish)
    def publish_decision(self):
        if self.state.qa_status == "APPROVED":
            return "publish"
        elif self.state.qa_status == "REWRITE":
            return "rewrite_content"
        else:
            return "reject"

    @listen("publish")
    def publish(self):
        return PublisherAgent.execute(self.state)

    @listen("rewrite_content")
    def rewrite_content(self):
        self.state.content_rewrite_count += 1
        if self.state.content_rewrite_count > 3:
            return self.reject()
        return self.generate_content()

    @listen("reject")
    def reject(self):
        IncidentService.archive(self.state, reason=self.state.reject_reason)
        AuditLogger.log("REJECT", self.state)

    @listen(publish)
    def track_analytics(self):
        return AnalyticsCrew.kickoff(inputs=self.state)
```

### 2.3 State Schema

```python
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ComplianceStatus(str, Enum):
    APPROVED = "APPROVED"
    REWRITE = "REWRITE"
    REJECT = "REJECT"

class PipelineState(BaseModel):
    product_id: str
    product_data: dict
    reference_ids: list[str] = []
    reference_type: Optional[str] = None
    compliance_status: Optional[ComplianceStatus] = None
    risk_score: float = 100.0
    creative_brief_id: Optional[str] = None
    asset_ids: list[str] = []
    script_id: Optional[str] = None
    caption: Optional[str] = None
    qa_status: Optional[ComplianceStatus] = None
    publish_status: Optional[str] = None
    platform_post_ids: dict[str, str] = {}
    experiment_id: Optional[str] = None
    rewrite_count: int = 0
    content_rewrite_count: int = 0
    reject_reason: Optional[str] = None
    audit_trail: list[dict] = []
```

### 2.4 Human Approval Checkpoints

Human approval is **optional but supported** at two gates:
1. **Post-rights-check**: Human can override REWRITE/REJECT with reason code.
2. **Pre-publish**: Human can review final asset bundle before publish.

Override must be logged with `override_reason_code`, `human_identity`, `timestamp`.

### 2.5 Retry/Recovery Rules

| Failure | Retry | Max | Backoff | Escalation |
|---------|-------|-----|---------|------------|
| API transient | Yes | 3 | Exponential 2^n sec | Queue + alert |
| Auth failure | No | 0 | — | Incident + halt |
| Policy reject | No | 0 | — | Archive + incident |
| Render failure | Yes | 2 | 30s | Manual queue |
| Rate limit | Yes | 5 | Platform-specific | Delay + alert |
| Rights uncertain | No | 0 | — | REWRITE or REJECT |

---

## SECTION 3 — AGENT LIST (DETAILED)

### Agent 1: Product Intake Agent

| Field | Value |
|-------|-------|
| **Role** | Product data ingestion specialist |
| **Goal** | Ingest Amazon product candidates from API, CSV, or manual input and produce structured product records |
| **Tools** | `amazon_paapi_tool`, `csv_parser_tool`, `product_db_writer` |
| **Inputs** | Raw product URL, ASIN, CSV file, or API search query |
| **Outputs** | `ProductRecord` (ASIN, title, price, category, images, description, affiliate_link) |
| **Guardrails** | Only use Amazon Product Advertising API (official). Never scrape. Validate ASIN format. |
| **KPIs** | Products ingested/day, data completeness score |
| **Fail Conditions** | Invalid ASIN, API auth failure, duplicate product |
| **Handoff** | → Product Enrichment Agent |

**Sample Prompt:**
```
You are the Product Intake Agent. Your job is to ingest Amazon product data.
RULES:
- Only use the Amazon Product Advertising API via the provided tool.
- Never scrape any website.
- Validate that every ASIN matches the format ^[A-Z0-9]{10}$.
- Output a structured ProductRecord with all required fields.
- If the API returns an error, report it; do not retry beyond the tool's built-in retry.
- Log every ingestion attempt to the audit trail.
INPUT: {product_input}
OUTPUT: ProductRecord JSON
```

### Agent 2: Product Enrichment Agent

| Field | Value |
|-------|-------|
| **Role** | Product context analyst |
| **Goal** | Enrich product records with category taxonomy, audience persona, use-case mapping, and trending signals |
| **Tools** | `category_taxonomy_tool`, `audience_persona_tool`, `trend_signal_tool` |
| **Inputs** | `ProductRecord` |
| **Outputs** | `EnrichedProduct` (original + category_path, primary_persona, use_cases[], trending_score) |
| **Guardrails** | No external scraping. Use only internal taxonomy and LLM reasoning. |
| **KPIs** | Enrichment completeness rate, persona accuracy (human-validated sample) |
| **Fail Conditions** | Unable to categorize product |
| **Handoff** | → Reference Intelligence Agent |

**Sample Prompt:**
```
You are the Product Enrichment Agent. Given a ProductRecord, determine:
1. Category path (e.g., Electronics > Audio > Headphones > Wireless)
2. Primary audience persona (e.g., "college student who loves anime and lo-fi music")
3. Top 3 use cases for this product
4. Trending relevance score (0-100)

RULES:
- Base your analysis ONLY on the product data provided.
- Do not make health/medical/financial claims.
- Output: EnrichedProduct JSON
INPUT: {product_record}
```

### Agent 3: Reference Intelligence Agent

| Field | Value |
|-------|-------|
| **Role** | Cultural reference mapper |
| **Goal** | Map enriched products to culturally resonant references from movies, anime, music, and novels that will drive engagement |
| **Tools** | `reference_graph_tool`, `public_domain_db_tool`, `trend_api_tool` |
| **Inputs** | `EnrichedProduct` |
| **Outputs** | `ReferenceBundle` (list of `Reference` objects with type, title, medium, risk_score, usage_mode) |
| **Guardrails** | Every reference MUST have a `reference_type` tag. Never recommend direct use of copyrighted material without license proof. Default to `style_only` when uncertain. |
| **KPIs** | Reference relevance score, audience resonance (post-engagement), rights-pass rate |
| **Fail Conditions** | No relevant references found (fallback to generic style/trope mode) |
| **Handoff** | → Rights & License Verification Agent |

**Sample Prompt:**
```
You are the Reference Intelligence Agent. Given an enriched product, find 3-5 culturally
relevant references that would resonate with the target audience.

FOR EACH REFERENCE, you MUST specify:
- title: The work/franchise name
- medium: anime | movie | music | novel | other
- reference_type: licensed_direct | public_domain | style_only | commentary
- usage_mode: What exactly can be used (e.g., "visual style inspired by", "direct quote under fair commentary")
- risk_score: 0-100 (0=safe, 100=dangerous)
- reasoning: Why this reference fits the product and audience

CRITICAL RULES:
- Default to style_only unless you have explicit license proof.
- Public domain works (pre-1928 US, or explicitly CC0) can be tagged public_domain.
- NEVER suggest using character names, logos, or signature visual elements as licensed_direct
  unless the rights_registry confirms a license.
- If no safe direct references exist, use style/trope/aesthetic references only.

INPUT: {enriched_product}
OUTPUT: ReferenceBundle JSON
```

### Agent 4: Rights & License Verification Agent

| Field | Value |
|-------|-------|
| **Role** | Compliance gatekeeper (DETERMINISTIC) |
| **Goal** | Verify that every reference in a ReferenceBundle is legally safe for commercial affiliate content |
| **Tools** | `rights_registry_tool`, `license_db_tool`, `public_domain_checker_tool` |
| **Inputs** | `ReferenceBundle` |
| **Outputs** | `RightsDecision` per reference: APPROVE / REWRITE / REJECT with reason and audit record |
| **Guardrails** | This is a DETERMINISTIC service. No LLM opinion on rights. Rules-based only. |
| **KPIs** | False-approve rate (must be 0%), decision speed |
| **Fail Conditions** | Unknown license status → REJECT. Missing provenance → REJECT. |
| **Handoff** | → Reference Risk Scoring Agent (if APPROVE), or back to Reference Intelligence Agent (if REWRITE) |

**Sample Prompt / Logic:**
```
RIGHTS VERIFICATION ENGINE (deterministic, not LLM-opinion):

FOR EACH reference IN bundle:
  1. Look up reference.title in rights_registry
  2. IF reference.reference_type == "licensed_direct":
       REQUIRE: license_record EXISTS AND license_record.expiry > NOW
                AND license_record.scope INCLUDES "commercial_social"
       IF NOT: decision = REJECT, reason = "No valid license for direct use"
  3. IF reference.reference_type == "public_domain":
       REQUIRE: public_domain_checker confirms public domain status
       IF NOT: decision = REJECT, reason = "Public domain status unconfirmed"
  4. IF reference.reference_type == "style_only":
       CHECK: reference does NOT include exact character names, logos,
              signature visual elements, trademarked phrases
       IF INCLUDES: decision = REWRITE, reason = "Remove specific IP elements"
       ELSE: decision = APPROVE
  5. IF reference.reference_type == "commentary":
       CHECK: usage is clearly commentary/review, not promotional impersonation
       IF ambiguous: decision = REWRITE
       ELSE: decision = APPROVE
  6. Log audit_event for every decision

OUTPUT: RightsDecision[] with compliance_status, reason, audit_id
```

**Example APPROVE Output:**
```json
{
  "reference_id": "ref-001",
  "title": "Pride and Prejudice",
  "reference_type": "public_domain",
  "decision": "APPROVE",
  "reason": "Published 1813. Confirmed public domain in all jurisdictions.",
  "risk_score": 5,
  "audit_id": "aud-7823",
  "timestamp": "2026-02-25T10:30:00Z"
}
```

**Example REWRITE Output:**
```json
{
  "reference_id": "ref-002",
  "title": "Demon Slayer",
  "reference_type": "style_only",
  "decision": "REWRITE",
  "reason": "Prompt includes character name 'Tanjiro'. Remove all character names and use generic style descriptors instead.",
  "risk_score": 65,
  "rewrite_instructions": "Replace character references with aesthetic descriptors: 'Japanese water-breathing sword art style' instead of 'Tanjiro's Water Breathing'",
  "audit_id": "aud-7824",
  "timestamp": "2026-02-25T10:30:01Z"
}
```

**Example REJECT Output:**
```json
{
  "reference_id": "ref-003",
  "title": "Spider-Man",
  "reference_type": "licensed_direct",
  "decision": "REJECT",
  "reason": "No license record found for Marvel/Spider-Man. Direct use of trademarked character in commercial content is prohibited.",
  "risk_score": 95,
  "audit_id": "aud-7825",
  "timestamp": "2026-02-25T10:30:02Z"
}
```

### Agent 5: Reference Risk Scoring Agent

| Field | Value |
|-------|-------|
| **Role** | Risk quantifier (DETERMINISTIC) |
| **Goal** | Assign a 0-100 risk score to each approved reference based on IP proximity, usage mode, and platform enforcement history |
| **Tools** | `risk_scoring_engine` |
| **Inputs** | `RightsDecision[]` (approved only) |
| **Outputs** | `ScoredReference[]` with final risk_score and auto_block flag |
| **Guardrails** | risk_score ≥ 70 → auto-block (REJECT). 40-69 → flag for human review. <40 → proceed. |
| **KPIs** | Correlation between risk score and actual takedown/complaint rate |
| **Fail Conditions** | Unable to score → treat as risk_score = 80 (block) |
| **Handoff** | → Creative Strategy Agent |

### Agent 6: Creative Strategy Agent

| Field | Value |
|-------|-------|
| **Role** | Content strategist |
| **Goal** | Choose the best content angle, format, and reference integration strategy for maximum engagement |
| **Tools** | `content_angle_selector`, `platform_trend_tool`, `competitor_analysis_tool` |
| **Inputs** | `EnrichedProduct`, `ScoredReference[]` |
| **Outputs** | `ContentBrief` (angle, format, target_platforms, reference_integration_plan, hook_strategy) |
| **Guardrails** | No deceptive claims. No fake scarcity. No health/medical claims without evidence. |
| **KPIs** | Brief-to-publish conversion rate, average engagement per brief |
| **Fail Conditions** | No viable angle found |
| **Handoff** | → Scriptwriter Agent |

### Agent 7: Scriptwriter Agent

| Field | Value |
|-------|-------|
| **Role** | Content scriptwriter |
| **Goal** | Write compelling short-form scripts based on the content brief |
| **Tools** | `script_template_tool`, `hook_library_tool`, `anti_repetition_checker` |
| **Inputs** | `ContentBrief` |
| **Outputs** | `Script` (hook, body_scenes[], cta, estimated_duration, content_hash) |
| **Guardrails** | No unverifiable claims. No fake testimonials. Scripts must include CTA with affiliate disclosure placeholder. Anti-repetition: similarity > 0.85 with existing scripts → REWRITE. |
| **KPIs** | Script approval rate, hook effectiveness (3s retention proxy) |
| **Fail Conditions** | Script too similar to existing content |
| **Handoff** | → Storyboard / Visual Prompt Agent |

**Sample Prompt:**
```
You are the Scriptwriter Agent. Write a short-form video script (15-60 seconds) based on the content brief.

CONTENT BRIEF: {content_brief}

STRUCTURE:
1. HOOK (first 3 seconds) — must stop the scroll
2. BODY (3-5 scenes) — demonstrate product value using the approved reference angle
3. CTA — clear call to action with {{AFFILIATE_DISCLOSURE}} placeholder

RULES:
- Never make claims you cannot verify from the product data.
- Never create fake testimonials or fake before/after scenarios.
- Never use exact copyrighted dialogue unless reference_type = licensed_direct.
- For style_only references, use aesthetic language without naming specific characters/works.
- Include {{AFFILIATE_DISCLOSURE}} in the CTA section.
- Keep total word count under 150 for a 30-second video.

OUTPUT: Script JSON with hook, scenes[], cta, word_count, estimated_duration_seconds
```

### Agent 8: Storyboard / Visual Prompt Agent

| Field | Value |
|-------|-------|
| **Role** | Visual direction specialist |
| **Goal** | Convert scripts into scene-by-scene visual prompts safe for image/video generation |
| **Tools** | `visual_prompt_compiler`, `reference_prompt_sanitizer`, `style_library_tool` |
| **Inputs** | `Script`, `ScoredReference[]` |
| **Outputs** | `Storyboard` (scene prompts[], style_guide, negative_prompts[]) |
| **Guardrails** | Visual prompts MUST NOT include copyrighted character names, trademarked logos, or signature elements unless reference_type = licensed_direct. Use the Reference Prompt Compiler to sanitize. |
| **KPIs** | Prompt-to-render success rate, visual quality score |
| **Fail Conditions** | Reference sanitizer flags unsafe elements |
| **Handoff** | → Asset Generation Coordinator Agent |

### Agent 9: Asset Generation Coordinator Agent

| Field | Value |
|-------|-------|
| **Role** | Rendering pipeline coordinator |
| **Goal** | Orchestrate image and video generation from visual prompts using approved generation APIs |
| **Tools** | `image_gen_api` (DALL-E/Midjourney/Stable Diffusion API), `video_gen_api`, `asset_storage_tool` |
| **Inputs** | `Storyboard` |
| **Outputs** | `AssetManifest` (asset_id, type, url, hash, generation_params, timestamp) |
| **Guardrails** | All generated assets get content-hashed. Signed URLs with 24h expiry. No asset published without QA. Worker isolation for rendering. |
| **KPIs** | Render success rate, asset quality score, generation cost per asset |
| **Fail Conditions** | Generation API failure, content policy violation from generation API |
| **Handoff** | → Video Assembly Agent |

### Agent 10: Video Assembly Agent

| Field | Value |
|-------|-------|
| **Role** | Video production service (DETERMINISTIC) |
| **Goal** | Assemble final video from generated assets, audio, and text overlays |
| **Tools** | `ffmpeg_tool`, `audio_gen_tool`, `subtitle_tool`, `asset_storage_tool` |
| **Inputs** | `AssetManifest`, `Script` |
| **Outputs** | `FinalVideo` (video_url, duration, resolution, format, hash) |
| **Guardrails** | Output must match platform specs. Audio must be royalty-free or licensed. |
| **KPIs** | Assembly success rate, output quality score |
| **Fail Conditions** | Asset missing, format incompatible |
| **Handoff** | → Caption + SEO + Disclosure Agent |

### Agent 11: Caption + SEO + Disclosure Agent

| Field | Value |
|-------|-------|
| **Role** | Caption and compliance copywriter |
| **Goal** | Generate platform-optimized captions with proper SEO, hashtags, and affiliate disclosures |
| **Tools** | `caption_generator`, `seo_keyword_tool`, `disclosure_template_tool`, `hashtag_optimizer` |
| **Inputs** | `ContentBrief`, `Script`, platform targets |
| **Outputs** | `CaptionBundle` (per-platform captions with disclosures embedded) |
| **Guardrails** | Every caption MUST include affiliate disclosure. No deceptive "organic" phrasing when affiliate links present. Disclosure format must comply with FTC guidelines and platform-specific rules. |
| **KPIs** | Disclosure compliance rate (must be 100%), caption engagement rate |
| **Fail Conditions** | Disclosure missing → auto-rewrite → re-QA |
| **Handoff** | → Platform Adaptation Agent |

**Sample Prompt:**
```
You are the Caption + SEO + Disclosure Agent. Write platform-specific captions.

CONTENT BRIEF: {content_brief}
SCRIPT SUMMARY: {script_summary}
TARGET PLATFORMS: {platforms}

FOR EACH PLATFORM, generate a caption with:
1. Hook line (matches video hook)
2. Value proposition (1-2 sentences)
3. Hashtags (platform-optimized, 3-10 tags)
4. Affiliate disclosure — MANDATORY, must be one of:
   - "#ad #affiliate"
   - "This post contains affiliate links. I may earn a commission at no extra cost to you."
   - Platform-specific required format
5. CTA with link placeholder {{AFFILIATE_LINK}}

RULES:
- NEVER omit the affiliate disclosure.
- NEVER phrase affiliate content as organic recommendation without disclosure.
- No fake urgency ("Only 2 left!" unless verified from product data).
- No health/medical claims.
- Adapt tone and length per platform:
  * TikTok: casual, short, emoji-friendly
  * Instagram: medium length, hashtag-heavy
  * X: under 280 chars, punchy
  * Pinterest: descriptive, keyword-rich

OUTPUT: CaptionBundle JSON with platform-keyed captions
```

### Agent 12: Platform Adaptation Agent

| Field | Value |
|-------|-------|
| **Role** | Platform format specialist |
| **Goal** | Adapt video/image assets and captions to each platform's technical requirements |
| **Tools** | `media_transcoder`, `platform_spec_tool`, `thumbnail_generator` |
| **Inputs** | `FinalVideo`, `CaptionBundle`, platform targets |
| **Outputs** | `PlatformPackage[]` (per-platform: media_file, caption, metadata, thumbnail) |
| **Guardrails** | Must meet platform technical specs. Must preserve disclosure in all variants. |
| **KPIs** | Platform accept rate, adaptation speed |
| **Fail Conditions** | Media fails platform validation |
| **Handoff** | → QA & Policy Checker Agent |

### Agent 13: QA & Policy Checker Agent

| Field | Value |
|-------|-------|
| **Role** | Final compliance gate (DETERMINISTIC) |
| **Goal** | Final check of all content against compliance rules, platform policies, and quality thresholds before publish |
| **Tools** | `compliance_checker`, `content_hash_dedup`, `disclosure_verifier`, `quality_scorer` |
| **Inputs** | `PlatformPackage[]` |
| **Outputs** | `QADecision` per package: APPROVE / REWRITE / REJECT |
| **Guardrails** | DETERMINISTIC checks: disclosure present? Duplicate hash? Rights approved? Risk score < threshold? Quality score > minimum? |
| **KPIs** | False-approve rate (must be 0%), QA throughput |
| **Fail Conditions** | Any check fails → REWRITE or REJECT |
| **Handoff** | → Publisher / Scheduler Agent (if APPROVE) |

**QA Checklist (deterministic):**
```
1. ✅ compliance_status == APPROVED for all references
2. ✅ risk_score < 40 for all references (or human-approved if 40-69)
3. ✅ affiliate_disclosure present in every caption
4. ✅ content_hash not duplicate of any published content on same platform
5. ✅ similarity_score < 0.85 vs recent content
6. ✅ media meets platform technical specs
7. ✅ no forbidden keywords/phrases detected
8. ✅ quality_score > 60 (0-100 scale)
9. ✅ all assets have valid signed URLs
10. ✅ audit trail complete for entire pipeline
```

### Agent 14: Publisher / Scheduler Agent

| Field | Value |
|-------|-------|
| **Role** | Platform publisher and scheduler |
| **Goal** | Publish approved content to target platforms via official APIs at optimal times |
| **Tools** | `tiktok_api_adapter`, `instagram_api_adapter`, `x_api_adapter`, `pinterest_api_adapter`, `scheduler_tool` |
| **Inputs** | `PlatformPackage[]` (QA-approved), scheduling preferences |
| **Outputs** | `PublishResult` (platform, post_id, status, timestamp, url) |
| **Guardrails** | Only publish QA-APPROVED content. Use official APIs only. Enforce posting cadence limits. Circuit-break on auth failures. |
| **KPIs** | Publish success rate, time-to-publish, cadence compliance |
| **Fail Conditions** | API auth failure → incident + halt. Rate limit → queue + delay. Policy reject → incident. |
| **Handoff** | → Analytics & Experimentation Agent |

**Sample Prompt / Logic:**
```
PUBLISHER AGENT (service logic):

1. VERIFY: qa_status == "APPROVED" for every package
   IF NOT: ABORT. Log security incident. Never publish unapproved content.

2. FOR EACH platform_package:
   a. Check posting_cadence: last_post_time + min_interval < NOW
   b. IF rate_limited: queue with retry_after timestamp
   c. Call platform_api_adapter.publish(package)
   d. IF success: log PublishResult, update post_queue status
   e. IF auth_error: create incident, halt all publishing for this platform
   f. IF rate_limit: re-queue with backoff
   g. IF policy_error: create incident, flag content for review
   h. IF transient_error: retry up to 3x with exponential backoff

3. Log audit_event for every publish attempt (success or failure)
```

### Agent 15: Analytics & Experimentation Agent

| Field | Value |
|-------|-------|
| **Role** | Performance analyst and experiment runner |
| **Goal** | Track content performance, run A/B experiments, and feed optimization signals back into the pipeline |
| **Tools** | `metrics_collector`, `experiment_engine`, `reporting_tool`, `optimization_recommender` |
| **Inputs** | `PublishResult[]`, platform analytics data, affiliate conversion data |
| **Outputs** | `PerformanceReport`, `ExperimentResult`, `OptimizationRecommendation` |
| **Guardrails** | Reddit-derived hypotheses are experimental priors, not facts. All experiment conclusions require statistical significance. |
| **KPIs** | Experiment velocity, optimization lift, attribution accuracy |
| **Fail Conditions** | Insufficient data for conclusions |
| **Handoff** | → Orchestrator (feeds back into product/reference selection) |

### Agent 16: Orchestrator / Manager Agent

| Field | Value |
|-------|-------|
| **Role** | Pipeline controller |
| **Goal** | Manage end-to-end flow, handle branching (APPROVE/REWRITE/REJECT), enforce retry limits, manage state |
| **Tools** | `flow_controller`, `state_manager`, `alert_tool`, `human_approval_tool` |
| **Inputs** | Pipeline triggers, state transitions, error signals |
| **Outputs** | Flow control decisions, state updates, alerts |
| **Guardrails** | Never skip compliance gates. Max rewrite loops = 3. Always log state transitions. |
| **KPIs** | Pipeline throughput, end-to-end latency, error rate |
| **Fail Conditions** | State corruption → halt + alert. Infinite loop detection. |
| **Handoff** | Manages all other agents |

---

## SECTION 4 — AGENTIC RULES (LEGAL/SAFE)

### Agent Constitution

Every agent in this system is bound by the following non-negotiable rules, derived from `Agents.md` and `Agents_Security.md`:

#### 4.1 ALLOWED Actions

```yaml
allowed_actions:
  - Use official platform APIs with valid credentials
  - Generate original creative content inspired by approved style references
  - Use public domain references freely
  - Use licensed references within license scope
  - Use style/aesthetic references without copying specific IP elements
  - Include clear affiliate disclosures in all commercial content
  - Log all decisions and actions to audit trail
  - Queue content for human review when uncertain
  - Retry transient API failures with backoff
  - Access secrets only from secrets manager
  - Generate signed URLs for media access
```

#### 4.2 FORBIDDEN Actions

```yaml
forbidden_actions:
  - NEVER use copyrighted character names/logos/signature elements without verified license
  - NEVER scrape websites or bypass platform restrictions
  - NEVER automate browser actions to circumvent ToS
  - NEVER publish content without compliance_status == APPROVED
  - NEVER create fake testimonials, reviews, or social proof
  - NEVER make fake scarcity claims ("Only 2 left!" without verification)
  - NEVER make health/medical/financial claims without evidence pipeline
  - NEVER omit affiliate disclosure from commercial content
  - NEVER phrase affiliate content as organic recommendation without disclosure
  - NEVER print, log, or expose secrets/tokens/API keys
  - NEVER store raw credentials in code, config files, or logs
  - NEVER bypass audit logging for any decision
  - NEVER publish duplicate content (same hash) to same platform
  - NEVER retry after policy rejection (create incident instead)
  - NEVER impersonate brands, creators, or public figures
  - NEVER evade rate limits, captchas, or review systems
  - NEVER access credentials beyond agent's RBAC role
```

#### 4.3 Escalation Rules

```yaml
escalation_rules:
  - rights_uncertain: REWRITE or REJECT (never publish)
  - api_auth_failure: halt + create incident + alert human
  - policy_rejection: stop retries + create incident
  - missing_disclosure: auto-rewrite caption + re-QA (no manual intervention needed)
  - dmca_notice: immediate takedown + incident + legal review queue
  - token_leak: rotate immediately + incident + audit all recent actions
  - repeated_failures (>3): halt pipeline segment + alert human
  - risk_score >= 70: auto-block (REJECT)
  - risk_score 40-69: flag for human review
  - unknown_error: log + alert + do NOT proceed
```

---

## SECTION 5 — SECURITY ARCHITECTURE

### 5.1 Security Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        SECRETS MANAGER                            │
│              (AWS Secrets Manager / HashiCorp Vault)               │
│   ┌──────────┬──────────┬──────────┬──────────┬──────────┐       │
│   │ Amazon   │ TikTok   │Instagram │    X     │Pinterest │       │
│   │ PA-API   │ API Keys │ API Keys │API Keys  │API Keys  │       │
│   │ Keys     │          │          │          │          │       │
│   └──────────┴──────────┴──────────┴──────────┴──────────┘       │
│   ┌──────────┬──────────┬──────────┐                              │
│   │ LLM API  │ Image Gen│ Storage  │                              │
│   │ Keys     │ API Keys │ Keys     │                              │
│   └──────────┴──────────┴──────────┘                              │
└────────────────────────────┬─────────────────────────────────────┘
                             │ (fetched at runtime, never stored in code)
┌────────────────────────────▼─────────────────────────────────────┐
│                        RBAC LAYER                                 │
│                                                                   │
│  ┌─────────────┬─────────────────────────────────────────────┐   │
│  │ Role        │ Permissions                                  │   │
│  ├─────────────┼─────────────────────────────────────────────┤   │
│  │ orchestrator│ flow control, state read/write, agent invoke │   │
│  │ compliance  │ rights_registry read, audit write, QA decide │   │
│  │ renderer    │ image_gen API, video_gen API, storage write  │   │
│  │ publisher   │ platform APIs (post only), schedule write    │   │
│  │ analyst     │ metrics read, experiment read/write          │   │
│  │ human-admin │ ALL + override + incident management         │   │
│  └─────────────┴─────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                     AUDIT LOG STORE                               │
│              (Immutable append-only log)                          │
│                                                                   │
│  Every event: {agent_id, action, input_hash, output_hash,        │
│                decision, timestamp, reason, session_id}           │
│                                                                   │
│  Retention: 7 years. Tamper detection via hash chain.             │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 Secrets Manager Usage

```python
# app/services/secrets.py
from functools import lru_cache
import boto3  # or hvac for Vault

class SecretsManager:
    """All credentials fetched at runtime. Never hardcoded."""

    def __init__(self, backend: str = "aws"):
        if backend == "aws":
            self._client = boto3.client("secretsmanager")
        # Add Vault, Azure Key Vault, etc.

    def get_secret(self, key: str) -> str:
        """Fetch secret by key. Cached for 5 min max."""
        response = self._client.get_secret_value(SecretId=key)
        return response["SecretString"]

    def get_platform_credentials(self, platform: str) -> dict:
        return json.loads(self.get_secret(f"affiliate-agency/{platform}"))
```

### 5.3 API Key Scope Separation

| Platform | Key Scope | Agent Access |
|----------|-----------|-------------|
| Amazon PA-API | Product search, item lookup | Product Intake only |
| TikTok | Content posting, analytics read | Publisher, Analyst |
| Instagram | Media upload, publish, insights | Publisher, Analyst |
| X | Tweet create, media upload, analytics | Publisher, Analyst |
| Pinterest | Pin create, board manage, analytics | Publisher, Analyst |
| OpenAI/LLM | Chat completions | Creative, Scriptwriter, Caption |
| Image Gen | Image generation | Renderer only |
| S3/Storage | Object read/write (scoped by prefix) | Renderer (write), all (signed read) |

### 5.4 Signed URLs for Media

```python
# All media access via signed URLs with expiry
def generate_signed_url(bucket: str, key: str, expiry_seconds: int = 86400) -> str:
    """Generate time-limited signed URL. Default 24h expiry."""
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiry_seconds,
    )
```

### 5.5 Hash-Based Asset Tracking

```python
import hashlib

def compute_content_hash(content: bytes) -> str:
    """SHA-256 hash for dedup and tamper detection."""
    return hashlib.sha256(content).hexdigest()

# Before publish: check hash against published_hashes[platform]
# If duplicate: REJECT with reason "duplicate_content"
```

### 5.6 Immutable Audit Logs

```python
@dataclass
class AuditEvent:
    event_id: str          # UUID
    timestamp: datetime     # UTC
    agent_id: str          # Which agent
    action: str            # What action
    input_hash: str        # SHA-256 of input
    output_hash: str       # SHA-256 of output
    decision: str          # APPROVE/REWRITE/REJECT/PUBLISH/etc.
    reason: str            # Human-readable reason
    session_id: str        # Pipeline run ID
    metadata: dict         # Additional context

# Stored in append-only table. No UPDATE or DELETE allowed.
# Hash-chained: each event includes hash of previous event.
```

### 5.7 Input Validation & Prompt Injection Defense

```python
class InputValidator:
    """Validate and sanitize all external inputs before agent processing."""

    FORBIDDEN_PATTERNS = [
        r"ignore\s+(previous|above)\s+instructions",
        r"system\s*prompt",
        r"<script>",
        r"javascript:",
        r"\{\{.*\}\}",  # Template injection
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise InputValidationError(f"Potentially malicious input detected")
        return text.strip()
```

### 5.8 Rate Limiting by Platform

| Platform | Rate Limit | Retry Strategy | Circuit Breaker |
|----------|-----------|----------------|-----------------|
| TikTok | Platform-defined | Exponential backoff, max 5 | Open after 3 consecutive failures, 15 min cooldown |
| Instagram | 25 posts/day | Linear backoff 60s, max 3 | Open after 3, 30 min cooldown |
| X | 300 tweets/3h | Exponential backoff, max 5 | Open after 5, 15 min cooldown |
| Pinterest | 50 pins/day | Linear backoff 30s, max 3 | Open after 3, 30 min cooldown |
| OpenAI | TPM/RPM limits | Exponential backoff, max 3 | Open after 3, 60s cooldown |

### 5.9 Incident Response Plans

#### DMCA Notice Received
```
1. IMMEDIATE: Take down cited content from all platforms
2. Log incident with full audit trail of content creation
3. Review rights_registry entry for the cited reference
4. If rights violation confirmed:
   a. Block reference permanently in rights_registry
   b. Review all content using same reference → takedown if needed
   c. Update risk scoring model
5. If fair use/false claim:
   a. Document counter-argument
   b. Queue for human-admin legal review
6. Notify human-admin within 1 hour
```

#### Account Restriction
```
1. IMMEDIATE: Halt all publishing to affected platform
2. Log incident with recent publishing history
3. Review last 10 published posts for policy violations
4. If violation found: remove violating content, adjust policies
5. If unclear: queue for human review
6. Do NOT attempt to create new accounts or circumvent restriction
7. Resume only after human-admin approval
```

#### Token Leak
```
1. IMMEDIATE: Rotate all potentially compromised credentials
2. Log incident with exposure scope
3. Audit all actions taken with compromised credentials
4. Review access logs for unauthorized usage
5. Update secrets manager with new credentials
6. Review and patch the leak vector
7. Notify human-admin immediately
```

---

## SECTION 6 — CLEAN CODE ARCHITECTURE

### 6.1 Project Structure

```
advertisement_agency/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Entry point
│   ├── config.py                  # Typed settings (Pydantic BaseSettings)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py          # Abstract base with guardrails
│   │   ├── product_intake.py
│   │   ├── product_enrichment.py
│   │   ├── reference_intelligence.py
│   │   ├── creative_strategy.py
│   │   ├── scriptwriter.py
│   │   ├── storyboard.py
│   │   ├── asset_coordinator.py
│   │   ├── caption_seo.py
│   │   ├── platform_adaptation.py
│   │   ├── publisher.py
│   │   ├── analytics.py
│   │   └── orchestrator.py
│   ├── flows/
│   │   ├── __init__.py
│   │   ├── content_pipeline.py    # Main CrewAI Flow
│   │   ├── reference_flow.py
│   │   ├── publish_flow.py
│   │   └── experiment_flow.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rights_engine.py       # Deterministic rights verification
│   │   ├── risk_scorer.py         # Deterministic risk scoring
│   │   ├── qa_checker.py          # Deterministic QA checks
│   │   ├── secrets.py             # Secrets manager wrapper
│   │   ├── audit_logger.py        # Immutable audit logging
│   │   ├── content_hasher.py      # Hash-based dedup
│   │   ├── media_signer.py        # Signed URL generation
│   │   ├── incident_manager.py    # Incident creation and tracking
│   │   └── scheduler.py           # Job scheduling
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base_adapter.py        # Abstract platform adapter
│   │   ├── amazon_adapter.py      # Amazon PA-API client
│   │   ├── tiktok_adapter.py
│   │   ├── instagram_adapter.py
│   │   ├── x_adapter.py
│   │   ├── pinterest_adapter.py
│   │   ├── image_gen_adapter.py   # DALL-E / SD adapter
│   │   ├── video_gen_adapter.py
│   │   └── storage_adapter.py     # S3/MinIO adapter
│   ├── policies/
│   │   ├── __init__.py
│   │   ├── agent_constitution.py  # Enforced rules
│   │   ├── disclosure_rules.py    # Affiliate disclosure policies
│   │   ├── platform_policies.py   # Per-platform content rules
│   │   └── rate_limits.py         # Rate limiting config
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── product.py             # ProductRecord, EnrichedProduct
│   │   ├── reference.py           # Reference, ReferenceBundle, ScoredReference
│   │   ├── rights.py              # RightsDecision, RightsRecord
│   │   ├── content.py             # ContentBrief, Script, Storyboard
│   │   ├── asset.py               # AssetManifest, FinalVideo
│   │   ├── caption.py             # CaptionBundle
│   │   ├── publish.py             # PlatformPackage, PublishResult
│   │   ├── analytics.py           # PerformanceMetrics, ExperimentResult
│   │   ├── audit.py               # AuditEvent
│   │   └── incident.py            # Incident
│   └── tools/
│       ├── __init__.py
│       ├── amazon_tools.py
│       ├── reference_tools.py
│       ├── rights_tools.py
│       ├── content_tools.py
│       ├── media_tools.py
│       ├── platform_tools.py
│       └── analytics_tools.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Shared fixtures
│   ├── unit/
│   │   ├── test_rights_engine.py
│   │   ├── test_risk_scorer.py
│   │   ├── test_qa_checker.py
│   │   ├── test_content_hasher.py
│   │   ├── test_disclosure_rules.py
│   │   ├── test_input_validator.py
│   │   └── test_schemas.py
│   └── integration/
│       ├── test_pipeline_flow.py
│       ├── test_reference_flow.py
│       ├── test_publish_flow.py
│       └── test_adapters.py
├── docs/                          # Auto-generated docs (see Section 13)
│   ├── phases/
│   ├── agents/
│   ├── tools/
│   ├── flows/
│   ├── compliance/
│   ├── security/
│   ├── adrs/
│   └── ops/
├── infra/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── terraform/
│   └── k8s/
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

### 6.2 Coding Standards

```toml
# pyproject.toml
[tool.ruff]
target-version = "py312"
line-length = 100
select = ["E", "F", "I", "N", "W", "UP", "S", "B", "A", "C4", "SIM", "TCH"]

[tool.mypy]
python_version = "3.12"
strict = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short --cov=app --cov-report=term-missing"
```

### 6.3 Key Design Principles

1. **Type hints everywhere** — All function signatures, return types, and Pydantic models.
2. **Structured logging** — Use `structlog` with JSON output. Never print secrets.
3. **Config via environment** — `pydantic-settings` with `.env` file. No hardcoded values.
4. **No business logic in prompts** — Agent prompts reference config/policy objects, not inline rules.
5. **Dependency injection** — Services receive dependencies via constructor, not global imports.
6. **Interface segregation** — Abstract base classes for adapters, services, agents.
7. **Test coverage** — Unit tests for all deterministic services. Integration tests for flows.

---

## SECTION 7 — REFERENCE INTELLIGENCE ENGINE

### 7.1 Product-to-Reference Mapping Pipeline

```
Product ──► Category ──► Use-Case ──► Audience Persona ──► Reference Graph
   │            │            │              │                     │
   │     "Wireless         "Music         "Gen-Z anime          Matches:
   │      Headphones"     listening,       fan, lo-fi            - Anime aesthetic
   │                       gaming,         music lover"          - Lo-fi music culture
   │                       commute"                              - Cyberpunk visual style
   │                                                             - Studio Ghibli (style_only)
```

### 7.2 Reference Graph Schema

```python
class Reference(BaseModel):
    reference_id: str                    # Unique ID
    title: str                           # Work/franchise name
    medium: Literal["anime", "movie", "music", "novel", "other"]
    reference_type: Literal["licensed_direct", "public_domain", "style_only", "commentary"]
    allowed_usage_mode: str              # e.g., "visual style inspiration only"
    risk_score: int                      # 0-100
    source_metadata: dict                # Where this mapping came from
    audience_overlap_score: float        # 0.0-1.0
    trending_relevance: float            # 0.0-1.0
    keywords: list[str]                  # Associated search/hashtag keywords
    fallback_references: list[str]       # IDs of safer alternatives
    created_at: datetime
    updated_at: datetime
```

### 7.3 Reference Prompt Compiler

The Reference Prompt Compiler converts approved references into generation-safe prompts by stripping copyrighted elements:

```python
class ReferencePromptCompiler:
    """Convert approved references into generation-safe visual/script prompts."""

    def compile(self, reference: ScoredReference, context: ContentBrief) -> str:
        if reference.reference_type == "licensed_direct":
            # Full use allowed within license scope
            return self._compile_licensed(reference, context)
        elif reference.reference_type == "public_domain":
            # Full use allowed
            return self._compile_public_domain(reference, context)
        elif reference.reference_type == "style_only":
            # Strip all specific IP, keep aesthetic descriptors
            return self._compile_style_only(reference, context)
        elif reference.reference_type == "commentary":
            # Frame as review/commentary context
            return self._compile_commentary(reference, context)

    def _compile_style_only(self, ref: ScoredReference, ctx: ContentBrief) -> str:
        """
        Example:
        Input reference: "Studio Ghibli" (style_only)
        Output prompt: "Whimsical hand-drawn animation style with soft watercolor
                        backgrounds, lush nature scenes, gentle lighting, and
                        nostalgic pastoral atmosphere"
        — No mention of "Studio Ghibli", "Totoro", "Spirited Away", etc.
        """
        style_descriptors = self._extract_style_descriptors(ref)
        sanitized = self._remove_ip_elements(style_descriptors)
        return self._build_prompt(sanitized, ctx)

    def _remove_ip_elements(self, descriptors: list[str]) -> list[str]:
        """Remove any trademarked names, character names, logos, signature elements."""
        blocked = self._load_blocked_terms()
        return [d for d in descriptors if not any(b in d.lower() for b in blocked)]
```

### 7.4 Fallback Strategy

When no safe direct references exist:
1. **Style/Trope Mode**: Use generic aesthetic descriptors ("dark academia", "cottagecore", "cyberpunk neon")
2. **Era/Movement Mode**: Reference art movements or historical periods ("Art Deco", "80s synth-wave aesthetic")
3. **Original Mode**: Generate completely original creative direction based on product attributes

---

## SECTION 8 — RIGHTS / LICENSING COMPLIANCE ENGINE

### 8.1 Rights Registry Schema

```sql
CREATE TABLE rights_registry (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_title VARCHAR(500) NOT NULL,
    reference_type  VARCHAR(50) NOT NULL CHECK (reference_type IN (
                        'licensed_direct', 'public_domain', 'style_only', 'commentary')),
    ip_owner        VARCHAR(500),             -- Rights holder
    license_id      VARCHAR(200),             -- External license reference
    license_scope   JSONB DEFAULT '{}',       -- {commercial: bool, social: bool, derivative: bool, ...}
    license_expiry  TIMESTAMP WITH TIME ZONE,
    territory       VARCHAR(100) DEFAULT 'worldwide',
    
    -- Status and scoring
    status          VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
                        'active', 'expired', 'revoked', 'pending', 'blocked')),
    risk_score      INTEGER DEFAULT 100 CHECK (risk_score BETWEEN 0 AND 100),
    auto_block      BOOLEAN DEFAULT false,
    
    -- Proof and provenance
    license_proof_url    VARCHAR(1000),       -- Link to license document
    provenance_chain     JSONB DEFAULT '[]',  -- Chain of custody / proof events
    
    -- Trademark specifics
    trademark_elements   JSONB DEFAULT '[]',  -- ["character_name", "logo", "catchphrase"]
    blocked_elements     JSONB DEFAULT '[]',  -- Specific elements that cannot be used
    
    -- Metadata
    notes           TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by      VARCHAR(100) NOT NULL
);

CREATE INDEX idx_rights_title ON rights_registry (reference_title);
CREATE INDEX idx_rights_type ON rights_registry (reference_type);
CREATE INDEX idx_rights_status ON rights_registry (status);
```

### 8.2 Rights Verification Logic (Deterministic)

```python
class RightsEngine:
    """Deterministic rights verification. No LLM opinion."""

    def verify(self, reference: Reference) -> RightsDecision:
        audit_event = AuditEvent(agent_id="rights_engine", action="verify")

        # Step 1: Look up in registry
        record = self.registry.lookup(reference.title)

        # Step 2: Type-specific checks
        if reference.reference_type == "licensed_direct":
            return self._check_licensed(reference, record, audit_event)
        elif reference.reference_type == "public_domain":
            return self._check_public_domain(reference, record, audit_event)
        elif reference.reference_type == "style_only":
            return self._check_style_only(reference, record, audit_event)
        elif reference.reference_type == "commentary":
            return self._check_commentary(reference, record, audit_event)

    def _check_licensed(self, ref, record, audit) -> RightsDecision:
        if not record or record.status != "active":
            return RightsDecision(decision="REJECT", reason="No active license found")
        if record.license_expiry and record.license_expiry < datetime.utcnow():
            return RightsDecision(decision="REJECT", reason="License expired")
        if not record.license_scope.get("commercial"):
            return RightsDecision(decision="REJECT", reason="License does not cover commercial use")
        if not record.license_scope.get("social"):
            return RightsDecision(decision="REJECT", reason="License does not cover social media")
        if not record.license_proof_url:
            return RightsDecision(decision="REJECT", reason="No license proof on file")
        return RightsDecision(decision="APPROVE", reason="Valid license with commercial+social scope")

    def _check_public_domain(self, ref, record, audit) -> RightsDecision:
        if not self.public_domain_checker.verify(ref.title):
            return RightsDecision(decision="REJECT", reason="Public domain status unconfirmed")
        return RightsDecision(decision="APPROVE", reason="Confirmed public domain")

    def _check_style_only(self, ref, record, audit) -> RightsDecision:
        # Check if any trademarked elements are referenced
        violations = self._find_ip_violations(ref)
        if violations:
            return RightsDecision(
                decision="REWRITE",
                reason=f"Remove IP elements: {violations}",
                rewrite_instructions=f"Replace {violations} with generic style descriptors"
            )
        return RightsDecision(decision="APPROVE", reason="Style reference with no IP elements")

    def _check_commentary(self, ref, record, audit) -> RightsDecision:
        if self._is_promotional_impersonation(ref):
            return RightsDecision(decision="REWRITE", reason="Commentary must not appear as brand endorsement")
        return RightsDecision(decision="APPROVE", reason="Legitimate commentary use")
```

### 8.3 Risk Score Thresholds

| Score Range | Action | Description |
|-------------|--------|-------------|
| 0-39 | APPROVE (auto) | Low risk, proceed automatically |
| 40-69 | REVIEW (flag) | Medium risk, flag for human review |
| 70-100 | REJECT (auto-block) | High risk, auto-block immediately |

### 8.4 Risk Scoring Formula

```python
def calculate_risk_score(reference: Reference, record: Optional[RightsRecord]) -> int:
    score = 0

    # Base score by reference type
    type_base = {
        "licensed_direct": 10 if record and record.status == "active" else 90,
        "public_domain": 5,
        "style_only": 20,
        "commentary": 30,
    }
    score += type_base.get(reference.reference_type, 50)

    # Modifiers
    if reference.reference_type != "public_domain":
        if not record:
            score += 30  # Unknown reference = risky
        if record and record.trademark_elements:
            score += len(record.trademark_elements) * 5  # Each TM element adds risk
        if record and record.auto_block:
            score = 100  # Hard block

    # Cap at 0-100
    return max(0, min(100, score))
```

---

## SECTION 9 — CONTENT GENERATION ENGINE

### 9.1 Script Templates by Content Angle

```python
SCRIPT_TEMPLATES = {
    "comparison": {
        "structure": ["hook_comparison", "product_a_scene", "product_b_scene", "verdict", "cta"],
        "hook_example": "Everyone says {product_a} is the best, but have you tried {product_b}?",
        "duration_target": 30,
    },
    "top_3": {
        "structure": ["hook_listicle", "item_1", "item_2", "item_3", "cta"],
        "hook_example": "3 things I wish I knew before buying {category}...",
        "duration_target": 45,
    },
    "story": {
        "structure": ["hook_narrative", "problem", "discovery", "transformation", "cta"],
        "hook_example": "I was about to give up on {use_case} until I found this...",
        "duration_target": 45,
    },
    "problem_solution": {
        "structure": ["hook_problem", "pain_point", "solution_reveal", "demo", "cta"],
        "hook_example": "Struggling with {problem}? Here's what actually works.",
        "duration_target": 30,
    },
    "aesthetic": {
        "structure": ["hook_visual", "aesthetic_showcase", "product_integration", "cta"],
        "hook_example": "POV: Your {use_case} setup hits different ✨",
        "duration_target": 20,
    },
    "meme_style": {
        "structure": ["hook_meme", "relatable_moment", "product_punchline", "cta"],
        "hook_example": "Me pretending I don't need {product} vs. me at 3am adding it to cart",
        "duration_target": 15,
    },
}
```

### 9.2 Visual Prompt Templates

```python
VISUAL_PROMPT_TEMPLATES = {
    "product_hero": "Clean product photography of {product_name}, {aesthetic_style}, "
                    "studio lighting, {color_palette}, minimalist background, 4K quality",
    "lifestyle": "{persona} using {product_name} in {setting}, {aesthetic_style}, "
                 "natural lighting, candid feel, warm tones",
    "aesthetic_flat_lay": "Flat lay arrangement with {product_name} and {complementary_items}, "
                          "{aesthetic_style}, overhead shot, {color_palette}",
    "before_after": "Split screen showing {problem_scene} vs {solution_scene} with {product_name}, "
                    "{aesthetic_style}, clear contrast",
    "reference_inspired": "{sanitized_style_description}, featuring {product_name} as focal point, "
                          "{mood}, {color_palette}, {composition_style}",
}
```

### 9.3 Video Generation Workflow

```
1. Script approved → Scene breakdown
2. Each scene → Visual prompt (via Reference Prompt Compiler)
3. Visual prompts → Image generation (DALL-E 3 / Stable Diffusion API)
4. Generated images → Quality check (resolution, content safety)
5. Images + Script → Video assembly (FFmpeg)
   a. Ken Burns effect on images
   b. Text overlay for hooks/CTAs
   c. Transitions between scenes
   d. Background music (royalty-free library)
6. Optional: TTS voiceover generation
7. Final render per platform spec
8. Content hash computed → dedup check
9. → QA pipeline
```

### 9.4 Anti-Repetition Logic

```python
class AntiRepetitionChecker:
    """Prevent duplicate or near-duplicate content."""

    SIMILARITY_THRESHOLD = 0.85  # Content with similarity > 85% is blocked

    def check(self, new_content_hash: str, new_script_text: str) -> bool:
        # Exact duplicate check
        if self.hash_store.exists(new_content_hash):
            return False  # BLOCKED: exact duplicate

        # Semantic similarity check against recent scripts
        recent_scripts = self.script_store.get_recent(days=30)
        for existing in recent_scripts:
            similarity = self._compute_similarity(new_script_text, existing.text)
            if similarity > self.SIMILARITY_THRESHOLD:
                return False  # BLOCKED: too similar

        return True  # APPROVED: sufficiently unique

    def _compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity of embeddings."""
        emb_a = self.embedding_model.encode(text_a)
        emb_b = self.embedding_model.encode(text_b)
        return float(np.dot(emb_a, emb_b) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b)))
```

### 9.5 Content Quality Scoring

```python
class ContentQualityScorer:
    """Score content quality before publish. Range: 0-100."""

    def score(self, package: PlatformPackage) -> int:
        scores = {
            "hook_strength": self._score_hook(package.script.hook),         # 0-25
            "visual_quality": self._score_visuals(package.assets),          # 0-25
            "script_coherence": self._score_script(package.script),         # 0-25
            "caption_quality": self._score_caption(package.caption),        # 0-15
            "disclosure_present": 10 if package.caption.has_disclosure else 0,  # 0-10
        }
        return sum(scores.values())

    # Minimum threshold: 60/100 to publish
```

---

## SECTION 10 — PLATFORM PUBLISHING LAYER

### 10.1 Platform Capability Matrix

| Capability | TikTok | Instagram | X (Twitter) | Pinterest |
|------------|--------|-----------|-------------|-----------|
| Video post | ✅ | ✅ (Reels) | ✅ | ✅ (Idea Pins) |
| Image post | ❌ | ✅ (Feed/Stories) | ✅ | ✅ (Pins) |
| Carousel | ❌ | ✅ | ❌ | ❌ |
| Max video length | 10 min | 90s (Reels) | 2:20 | 5 min |
| Aspect ratio | 9:16 | 9:16 / 1:1 | 16:9 / 1:1 | 2:3 / 9:16 |
| Link in post | Bio only | Bio / Story link | ✅ | ✅ |
| Hashtag limit | ~5-8 | 30 | ~3-5 | 20 |
| API publish | Content Posting API | Instagram Graph API | X API v2 | Pinterest API v5 |
| Analytics API | TikTok for Business | Insights API | Analytics API | Analytics API |

### 10.2 Platform Adapter Design

```python
from abc import ABC, abstractmethod

class PlatformAdapter(ABC):
    """Abstract base for all platform publishing adapters."""

    @abstractmethod
    async def publish(self, package: PlatformPackage) -> PublishResult:
        """Publish content to platform. Returns result with post_id or error."""
        ...

    @abstractmethod
    async def get_analytics(self, post_id: str) -> dict:
        """Fetch analytics for a published post."""
        ...

    @abstractmethod
    def validate_media(self, media_path: str) -> bool:
        """Validate media meets platform specs."""
        ...

    @abstractmethod
    def format_caption(self, caption: str) -> str:
        """Format caption to meet platform character/format limits."""
        ...


class TikTokAdapter(PlatformAdapter):
    """TikTok Content Posting API adapter."""

    def __init__(self, secrets: SecretsManager):
        self.credentials = secrets.get_platform_credentials("tiktok")
        self.rate_limiter = RateLimiter(platform="tiktok")
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=900
        )

    async def publish(self, package: PlatformPackage) -> PublishResult:
        if self.circuit_breaker.is_open:
            return PublishResult(status="QUEUED", reason="Circuit breaker open")

        await self.rate_limiter.acquire()

        try:
            # Step 1: Initialize upload
            init_response = await self._init_upload(package.media_size)
            # Step 2: Upload media
            await self._upload_chunks(init_response.upload_url, package.media_path)
            # Step 3: Publish with caption
            result = await self._publish_video(
                init_response.publish_id,
                caption=package.caption,
            )
            self.circuit_breaker.record_success()
            return PublishResult(
                platform="tiktok",
                post_id=result.id,
                status="PUBLISHED",
                url=result.url,
                timestamp=datetime.utcnow(),
            )
        except AuthError as e:
            self.circuit_breaker.record_failure()
            raise IncidentError("AUTH", f"TikTok auth failure: {e}")
        except RateLimitError as e:
            return PublishResult(status="RATE_LIMITED", retry_after=e.retry_after)
        except PolicyError as e:
            raise IncidentError("POLICY", f"TikTok policy rejection: {e}")
        except TransientError as e:
            self.circuit_breaker.record_failure()
            return PublishResult(status="TRANSIENT_ERROR", reason=str(e))
```

### 10.3 Error Taxonomy

```python
class PublishErrorType(str, Enum):
    AUTH = "AUTH"                  # Credentials invalid/expired → Incident + halt
    RATE_LIMIT = "RATE_LIMIT"     # Too many requests → Queue + backoff
    VALIDATION = "VALIDATION"     # Media/caption doesn't meet specs → Adapt + retry
    POLICY = "POLICY"             # Content policy violation → Incident + review
    TRANSIENT = "TRANSIENT"       # Network/server error → Retry with backoff
```

### 10.4 Manual Queue Fallback

When API publishing is unavailable (no API access, sustained auth failures, etc.):
```python
class ManualPublishQueue:
    """Queue content for human manual publishing."""

    def enqueue(self, package: PlatformPackage, reason: str) -> str:
        queue_item = {
            "id": str(uuid4()),
            "platform": package.platform,
            "media_url": package.signed_media_url,  # Time-limited signed URL
            "caption": package.caption,
            "scheduled_time": package.scheduled_time,
            "reason": reason,
            "status": "pending_manual",
            "created_at": datetime.utcnow(),
        }
        self.db.insert("manual_publish_queue", queue_item)
        self.notify_human(queue_item)
        return queue_item["id"]
```

---

## SECTION 11 — ANALYTICS & EXPERIMENTATION

### 11.1 Event Tracking Model

```python
class ContentEvent(BaseModel):
    event_id: str
    post_id: str
    platform: str
    event_type: Literal[
        "impression", "view", "like", "comment", "share",
        "save", "click", "affiliate_click", "affiliate_conversion",
        "watch_25", "watch_50", "watch_75", "watch_100",
    ]
    value: Optional[float] = None        # e.g., conversion amount
    timestamp: datetime
    metadata: dict = {}

class PerformanceMetrics(BaseModel):
    post_id: str
    platform: str
    impressions: int = 0
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    ctr: float = 0.0                    # clicks / impressions
    watch_time_avg: Optional[float] = None
    affiliate_clicks: int = 0
    affiliate_conversions: int = 0
    affiliate_revenue: float = 0.0
    collected_at: datetime
```

### 11.2 Experiment Framework

```python
class Experiment(BaseModel):
    experiment_id: str
    name: str
    hypothesis: str                      # What we're testing
    hypothesis_source: Literal["data", "reddit", "intuition", "competitor"]
    experiment_type: Literal[
        "hook_ab", "reference_type_ab", "caption_ab",
        "posting_time_ab", "angle_ab", "platform_ab"
    ]
    variants: list[ExperimentVariant]    # Control + treatments
    traffic_split: dict[str, float]      # {"control": 0.5, "treatment_a": 0.5}
    start_date: datetime
    end_date: Optional[datetime]
    min_sample_size: int                 # Per variant
    status: Literal["draft", "running", "completed", "stopped"]
    results: Optional[ExperimentResult] = None

class ExperimentVariant(BaseModel):
    variant_id: str
    name: str                            # "control", "treatment_a"
    content_config: dict                 # What's different in this variant
    sample_count: int = 0
    metrics: Optional[PerformanceMetrics] = None

class ExperimentResult(BaseModel):
    winning_variant: Optional[str]
    p_value: float
    confidence_level: float
    lift_percentage: float               # % improvement over control
    sample_size_met: bool
    recommendation: Literal["promote", "pause", "rewrite", "inconclusive"]
```

### 11.3 Optimization Loop

```
1. Collect metrics for all published posts (daily sync)
2. Score posts: engagement_score = weighted(views, likes, shares, saves, clicks, conversions)
3. Classify outcomes:
   - TOP performers (top 20%) → Promote: create similar content, boost
   - MID performers (middle 60%) → Maintain: continue posting
   - LOW performers (bottom 20%) → Analyze: what went wrong?
     - Bad hook → rewrite hook, re-test
     - Bad reference → try different reference angle
     - Bad timing → adjust schedule
     - Bad platform → deprioritize platform for this niche
4. Feed learnings back into Creative Strategy Agent
5. Update experiment priors

NOTE: Reddit-derived hypotheses (e.g., "posting at 7 PM EST gets more views")
are treated as EXPERIMENTAL PRIORS, not facts. They must be validated via A/B tests.
```

---

## SECTION 12 — DATA MODELS / SCHEMAS

### 12.1 SQL Schemas

```sql
-- PRODUCTS
CREATE TABLE products (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asin        VARCHAR(10) UNIQUE NOT NULL,
    title       VARCHAR(1000) NOT NULL,
    price       DECIMAL(10,2),
    currency    VARCHAR(3) DEFAULT 'USD',
    category    VARCHAR(500),
    category_path JSONB DEFAULT '[]',
    description TEXT,
    image_urls  JSONB DEFAULT '[]',
    affiliate_link VARCHAR(2000),
    primary_persona VARCHAR(500),
    use_cases   JSONB DEFAULT '[]',
    trending_score INTEGER DEFAULT 0,
    status      VARCHAR(50) DEFAULT 'active',
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- REFERENCES
CREATE TABLE references (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(500) NOT NULL,
    medium          VARCHAR(50) NOT NULL,
    reference_type  VARCHAR(50) NOT NULL,
    allowed_usage_mode TEXT,
    risk_score      INTEGER DEFAULT 100,
    audience_overlap_score FLOAT DEFAULT 0.0,
    trending_relevance FLOAT DEFAULT 0.0,
    keywords        JSONB DEFAULT '[]',
    fallback_ids    JSONB DEFAULT '[]',
    source_metadata JSONB DEFAULT '{}',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RIGHTS REGISTRY (see Section 8 for full schema)

-- CONTENT BRIEFS
CREATE TABLE content_briefs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id      UUID REFERENCES products(id),
    reference_ids   JSONB DEFAULT '[]',
    angle           VARCHAR(100),
    format          VARCHAR(50),
    target_platforms JSONB DEFAULT '[]',
    hook_strategy   TEXT,
    reference_integration_plan TEXT,
    status          VARCHAR(50) DEFAULT 'draft',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- SCRIPTS
CREATE TABLE scripts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id        UUID REFERENCES content_briefs(id),
    hook            TEXT NOT NULL,
    scenes          JSONB DEFAULT '[]',
    cta             TEXT,
    word_count      INTEGER,
    estimated_duration_seconds INTEGER,
    content_hash    VARCHAR(64),
    similarity_checked BOOLEAN DEFAULT false,
    version         INTEGER DEFAULT 1,
    status          VARCHAR(50) DEFAULT 'draft',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ASSET MANIFEST
CREATE TABLE asset_manifest (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    script_id       UUID REFERENCES scripts(id),
    asset_type      VARCHAR(50) NOT NULL, -- image, video, audio, thumbnail
    storage_key     VARCHAR(1000) NOT NULL,
    content_hash    VARCHAR(64) NOT NULL,
    mime_type       VARCHAR(100),
    file_size_bytes BIGINT,
    resolution      VARCHAR(20),
    duration_seconds FLOAT,
    generation_params JSONB DEFAULT '{}',
    status          VARCHAR(50) DEFAULT 'generated',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- POST QUEUE
CREATE TABLE post_queue (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id        UUID REFERENCES asset_manifest(id),
    platform        VARCHAR(50) NOT NULL,
    caption         TEXT NOT NULL,
    scheduled_time  TIMESTAMP WITH TIME ZONE,
    priority        INTEGER DEFAULT 0,
    qa_status       VARCHAR(50) DEFAULT 'pending',
    compliance_status VARCHAR(50) DEFAULT 'pending',
    retry_count     INTEGER DEFAULT 0,
    max_retries     INTEGER DEFAULT 3,
    status          VARCHAR(50) DEFAULT 'queued',
    error_type      VARCHAR(50),
    error_message   TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- PUBLISHED POSTS
CREATE TABLE published_posts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id        UUID REFERENCES post_queue(id),
    platform        VARCHAR(50) NOT NULL,
    platform_post_id VARCHAR(500),
    post_url        VARCHAR(2000),
    content_hash    VARCHAR(64),
    published_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status          VARCHAR(50) DEFAULT 'live'
);

-- PERFORMANCE METRICS
CREATE TABLE performance_metrics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    published_post_id UUID REFERENCES published_posts(id),
    platform        VARCHAR(50) NOT NULL,
    impressions     INTEGER DEFAULT 0,
    views           INTEGER DEFAULT 0,
    likes           INTEGER DEFAULT 0,
    comments        INTEGER DEFAULT 0,
    shares          INTEGER DEFAULT 0,
    saves           INTEGER DEFAULT 0,
    clicks          INTEGER DEFAULT 0,
    ctr             FLOAT DEFAULT 0.0,
    watch_time_avg  FLOAT,
    affiliate_clicks INTEGER DEFAULT 0,
    affiliate_conversions INTEGER DEFAULT 0,
    affiliate_revenue DECIMAL(10,2) DEFAULT 0.00,
    collected_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- EXPERIMENTS
CREATE TABLE experiments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(500) NOT NULL,
    hypothesis      TEXT NOT NULL,
    hypothesis_source VARCHAR(50),
    experiment_type VARCHAR(100),
    variants        JSONB DEFAULT '[]',
    traffic_split   JSONB DEFAULT '{}',
    min_sample_size INTEGER DEFAULT 100,
    start_date      TIMESTAMP WITH TIME ZONE,
    end_date        TIMESTAMP WITH TIME ZONE,
    status          VARCHAR(50) DEFAULT 'draft',
    results         JSONB,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- INCIDENTS
CREATE TABLE incidents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_type   VARCHAR(100) NOT NULL, -- dmca, policy_violation, token_leak, etc.
    severity        VARCHAR(50) DEFAULT 'medium',
    description     TEXT NOT NULL,
    affected_posts  JSONB DEFAULT '[]',
    affected_platforms JSONB DEFAULT '[]',
    resolution      TEXT,
    status          VARCHAR(50) DEFAULT 'open',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at     TIMESTAMP WITH TIME ZONE,
    created_by      VARCHAR(100)
);

-- AUDIT EVENTS (IMMUTABLE — No UPDATE/DELETE allowed)
CREATE TABLE audit_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        VARCHAR(100) NOT NULL,
    action          VARCHAR(200) NOT NULL,
    input_hash      VARCHAR(64),
    output_hash     VARCHAR(64),
    decision        VARCHAR(50),
    reason          TEXT,
    session_id      VARCHAR(100),
    previous_event_hash VARCHAR(64), -- Hash chain for tamper detection
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prevent modifications to audit events
REVOKE UPDATE, DELETE ON audit_events FROM PUBLIC;
```

### 12.2 JSON Examples

**Product Record:**
```json
{
  "id": "prod-001",
  "asin": "B09V3KXJPB",
  "title": "Sony WH-1000XM5 Wireless Noise Canceling Headphones",
  "price": 348.00,
  "currency": "USD",
  "category": "Electronics",
  "category_path": ["Electronics", "Audio", "Headphones", "Over-Ear", "Noise Canceling"],
  "primary_persona": "Remote worker / audiophile who values premium sound and quiet focus",
  "use_cases": ["work-from-home calls", "music listening", "travel noise isolation"],
  "trending_score": 78,
  "affiliate_link": "https://www.amazon.com/dp/B09V3KXJPB?tag=myaffiliate-20"
}
```

**Reference Bundle:**
```json
{
  "product_id": "prod-001",
  "references": [
    {
      "reference_id": "ref-101",
      "title": "Lo-fi Hip Hop aesthetic",
      "medium": "music",
      "reference_type": "style_only",
      "allowed_usage_mode": "Visual style inspiration: cozy desk setup, warm lighting, animated study scene aesthetic",
      "risk_score": 15,
      "audience_overlap_score": 0.85,
      "keywords": ["lofi", "study", "chill", "aesthetic"]
    },
    {
      "reference_id": "ref-102",
      "title": "Blade Runner (1982 visual style)",
      "medium": "movie",
      "reference_type": "style_only",
      "allowed_usage_mode": "Cyberpunk neon aesthetic only. No character likenesses, no quotes, no logos.",
      "risk_score": 25,
      "audience_overlap_score": 0.65,
      "keywords": ["cyberpunk", "neon", "futuristic", "tech"]
    }
  ]
}
```

**Audit Event:**
```json
{
  "id": "aud-9001",
  "agent_id": "rights_engine",
  "action": "verify_reference",
  "input_hash": "a3f2b8c1d4e5...",
  "output_hash": "f7a9c3b2e1d6...",
  "decision": "APPROVE",
  "reason": "Style reference with no IP elements detected",
  "session_id": "pipeline-run-2026-02-25-001",
  "previous_event_hash": "b2c3d4e5f6a7...",
  "metadata": {
    "reference_id": "ref-101",
    "reference_type": "style_only",
    "risk_score": 15
  },
  "created_at": "2026-02-25T10:30:00Z"
}
```

---

## SECTION 13 — DOCUMENTATION GENERATION PLAN

### 13.1 Docs Folder Structure

```
docs/
├── phases/
│   ├── phase-01-mvp.md
│   ├── phase-02-reference-engine.md
│   ├── phase-03-video-publishing.md
│   ├── phase-04-analytics.md
│   └── phase-05-scale.md
├── agents/
│   ├── product-intake.md
│   ├── product-enrichment.md
│   ├── reference-intelligence.md
│   ├── rights-verification.md
│   ├── risk-scoring.md
│   ├── creative-strategy.md
│   ├── scriptwriter.md
│   ├── storyboard.md
│   ├── asset-coordinator.md
│   ├── video-assembly.md
│   ├── caption-seo.md
│   ├── platform-adaptation.md
│   ├── qa-policy.md
│   ├── publisher.md
│   ├── analytics.md
│   └── orchestrator.md
├── tools/
│   ├── amazon-paapi.md
│   ├── image-generation.md
│   ├── video-generation.md
│   ├── tiktok-api.md
│   ├── instagram-api.md
│   ├── x-api.md
│   └── pinterest-api.md
├── flows/
│   ├── content-pipeline.md
│   ├── reference-flow.md
│   ├── publish-flow.md
│   └── experiment-flow.md
├── compliance/
│   ├── rights-and-disclosure.md
│   └── platform-policies.md
├── security/
│   ├── threat-model.md
│   ├── secrets-policy.md
│   ├── rbac-matrix.md
│   └── incident-runbooks.md
├── ops/
│   ├── daily-runbook.md
│   ├── weekly-review.md
│   └── on-call-incidents.md
└── adrs/
    ├── ADR-0001-crewai-orchestration.md
    ├── ADR-0002-deterministic-compliance.md
    ├── ADR-0003-queue-selection.md
    ├── ADR-0004-storage-architecture.md
    └── ADR-0005-rendering-engine.md
```

### 13.2 Template: Phase Doc

```markdown
# Phase XX: {Phase Name}

## Objective
{What this phase achieves}

## Scope
{What's included and excluded}

## Architecture Changes
{New components, modified components, removed components}

## Modules Added/Changed
| Module | Change Type | Description |
|--------|------------|-------------|
| ...    | Added      | ...         |

## Data Schema Changes
{New tables, modified columns, migrations}

## Tests Added
| Test File | Coverage | Description |
|-----------|----------|-------------|
| ...       | ...      | ...         |

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ...  | ...       | ...    | ...        |

## Rollback Steps
1. {Step 1}
2. {Step 2}

## Next Phase Dependencies
{What the next phase requires from this one}
```

### 13.3 Template: Agent Doc

```markdown
# Agent: {Agent Name}

## Purpose
{What this agent does}

## Prompt Version
{Version hash and changelog}

## Inputs
| Field | Type | Required | Description |
|-------|------|----------|-------------|

## Outputs
| Field | Type | Description |
|-------|------|-------------|

## Tools Used
| Tool | Purpose | Auth Required |
|------|---------|--------------|

## Guardrails
- {Rule 1}
- {Rule 2}

## Failure Modes
| Failure | Detection | Response |
|---------|-----------|----------|

## Example Outputs

### APPROVE
```json
{...}
```

### REWRITE
```json
{...}
```

### REJECT
```json
{...}
```

## KPIs & Monitoring
| KPI | Target | Alert Threshold |
|-----|--------|-----------------|
```

### 13.4 Template: Tool Doc

```markdown
# Tool: {Tool Name}

## Auth Method
{API key, OAuth, etc.}

## API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|

## Rate Limits
{Requests/second, daily quota}

## Request Schema
```json
{...}
```

## Response Schema
```json
{...}
```

## Retries & Backoff
{Strategy, max retries, backoff formula}

## Common Errors
| Error | Cause | Resolution |
|-------|-------|------------|

## Fallback Behavior
{What happens when the tool is unavailable}
```

### 13.5 Template: ADR

```markdown
# ADR-XXXX: {Title}

## Status
{Proposed | Accepted | Deprecated | Superseded}

## Context
{Why this decision was needed}

## Decision
{What was decided}

## Consequences
{Positive and negative impacts}

## Alternatives Considered
| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|-------------|
```

---

## SECTION 14 — IMPLEMENTATION ROADMAP

### Phase 1: MVP (Weeks 1-3)
**Product → Script → Caption → Manual Publish**

#### Tasks
1. Set up project structure and dependencies
2. Implement `ProductRecord` and `EnrichedProduct` schemas
3. Build Product Intake Agent (manual CSV + basic ASIN lookup)
4. Build Product Enrichment Agent (category + persona mapping)
5. Build Scriptwriter Agent (2-3 script templates)
6. Build Caption + Disclosure Agent (with mandatory disclosure)
7. Implement basic QA Checker (disclosure verification, quality threshold)
8. Build manual publish queue (generate files for human to post)
9. Set up audit logging (basic)
10. Set up structured logging

#### Code Modules
- `app/schemas/product.py`
- `app/schemas/content.py`
- `app/schemas/audit.py`
- `app/agents/product_intake.py`
- `app/agents/product_enrichment.py`
- `app/agents/scriptwriter.py`
- `app/agents/caption_seo.py`
- `app/services/qa_checker.py`
- `app/services/audit_logger.py`
- `app/policies/disclosure_rules.py`
- `app/config.py`

#### Tests
- `tests/unit/test_schemas.py`
- `tests/unit/test_qa_checker.py`
- `tests/unit/test_disclosure_rules.py`
- `tests/integration/test_mvp_flow.py`

#### Docs to Generate
- `docs/phases/phase-01-mvp.md`
- `docs/agents/product-intake.md`
- `docs/agents/scriptwriter.md`
- `docs/agents/caption-seo.md`
- `docs/adrs/ADR-0001-crewai-orchestration.md`

#### Exit Criteria
- Can ingest a product and produce a script + caption with disclosure
- QA checker blocks content without disclosure
- Audit log captures all pipeline events
- Manual publish queue generates download-ready content packages

#### Risks & Rollback
| Risk | Mitigation | Rollback |
|------|-----------|----------|
| CrewAI API changes | Pin exact version | Fall back to direct LLM calls |
| LLM produces unsafe content | QA checker filters | Manual review all output |
| Schema changes needed | Use migrations | Revert migration |

---

### Phase 2: Reference Engine + Rights Registry (Weeks 4-6)
**Add cultural reference mapping and compliance validation**

#### Tasks
1. Implement `Reference` and `ReferenceBundle` schemas
2. Build Reference Intelligence Agent
3. Build Rights Registry (database + service)
4. Build Rights Engine (deterministic verification)
5. Build Risk Scoring Engine
6. Build Reference Prompt Compiler
7. Integrate reference flow into main pipeline
8. Add rights-based APPROVE/REWRITE/REJECT branching

#### Code Modules
- `app/schemas/reference.py`
- `app/schemas/rights.py`
- `app/agents/reference_intelligence.py`
- `app/services/rights_engine.py`
- `app/services/risk_scorer.py`
- `app/services/reference_prompt_compiler.py`
- `app/flows/reference_flow.py`

#### Tests
- `tests/unit/test_rights_engine.py`
- `tests/unit/test_risk_scorer.py`
- `tests/unit/test_reference_prompt_compiler.py`
- `tests/integration/test_reference_flow.py`

#### Docs to Generate
- `docs/phases/phase-02-reference-engine.md`
- `docs/agents/reference-intelligence.md`
- `docs/agents/rights-verification.md`
- `docs/compliance/rights-and-disclosure.md`
- `docs/adrs/ADR-0002-deterministic-compliance.md`

#### Exit Criteria
- Products are mapped to 3-5 relevant references
- Every reference has a risk score and compliance decision
- Style-only references produce safe prompts (no IP elements)
- REWRITE loop works correctly (max 3 iterations)
- REJECT properly archives with reason and audit trail

#### Risks & Rollback
| Risk | Mitigation | Rollback |
|------|-----------|----------|
| Rights data incomplete | Default to REJECT on unknown | Block all references until data populated |
| Reference mapping irrelevant | Human review sample weekly | Fall back to generic style/trope mode |

---

### Phase 3: Video Rendering + API Publishing (Weeks 7-10)
**Add image/video generation and platform API integration**

#### Tasks
1. Build Storyboard / Visual Prompt Agent
2. Build Asset Generation Coordinator (image gen API integration)
3. Build Video Assembly Service (FFmpeg pipeline)
4. Build Platform Adapters (TikTok, Instagram, X, Pinterest)
5. Build Publisher / Scheduler Agent
6. Implement signed URLs for media
7. Implement content hash dedup
8. Build anti-repetition checker
9. Set up secrets manager integration
10. Implement RBAC for publisher credentials

#### Code Modules
- `app/agents/storyboard.py`
- `app/agents/asset_coordinator.py`
- `app/agents/publisher.py`
- `app/services/video_assembly.py`
- `app/services/content_hasher.py`
- `app/services/media_signer.py`
- `app/services/secrets.py`
- `app/adapters/tiktok_adapter.py`
- `app/adapters/instagram_adapter.py`
- `app/adapters/x_adapter.py`
- `app/adapters/pinterest_adapter.py`
- `app/adapters/image_gen_adapter.py`
- `app/adapters/storage_adapter.py`
- `app/policies/rate_limits.py`

#### Tests
- `tests/unit/test_content_hasher.py`
- `tests/unit/test_anti_repetition.py`
- `tests/integration/test_publish_flow.py`
- `tests/integration/test_adapters.py` (with mocks)

#### Docs to Generate
- `docs/phases/phase-03-video-publishing.md`
- `docs/tools/tiktok-api.md`
- `docs/tools/instagram-api.md`
- `docs/tools/x-api.md`
- `docs/tools/pinterest-api.md`
- `docs/tools/image-generation.md`
- `docs/security/secrets-policy.md`
- `docs/security/rbac-matrix.md`
- `docs/flows/publish-flow.md`

#### Exit Criteria
- Images generated from visual prompts
- Videos assembled from images + text + audio
- At least one platform adapter publishes successfully
- Content hash prevents duplicates
- Signed URLs work with 24h expiry
- RBAC restricts publisher credentials to publisher agent only

#### Risks & Rollback
| Risk | Mitigation | Rollback |
|------|-----------|----------|
| Platform API access denied | Apply early, have manual fallback | Manual publish queue |
| Image gen produces unsafe output | Content safety filter + QA | Block and regenerate |
| High rendering costs | Budget alerts, batch optimization | Reduce render volume |

---

### Phase 4: Analytics + Experimentation (Weeks 11-13)
**Add performance tracking and A/B testing**

#### Tasks
1. Build Analytics & Experimentation Agent
2. Implement event tracking model
3. Build experiment framework (A/B config, traffic splitting)
4. Build optimization recommender
5. Connect platform analytics APIs
6. Build reporting dashboard data layer
7. Implement experiment statistical analysis

#### Code Modules
- `app/agents/analytics.py`
- `app/schemas/analytics.py`
- `app/services/metrics_collector.py`
- `app/services/experiment_engine.py`
- `app/services/optimization_recommender.py`
- `app/flows/experiment_flow.py`

#### Tests
- `tests/unit/test_experiment_engine.py`
- `tests/unit/test_optimization.py`
- `tests/integration/test_analytics_flow.py`

#### Docs to Generate
- `docs/phases/phase-04-analytics.md`
- `docs/agents/analytics.md`
- `docs/flows/experiment-flow.md`

#### Exit Criteria
- Metrics collected for all published posts
- A/B experiments can be configured and run
- Statistical significance calculated for experiment results
- Optimization recommendations generated from data

---

### Phase 5: Scale (Weeks 14-18)
**Queue-based processing, worker isolation, multi-niche**

#### Tasks
1. Add message queue (Redis Streams / SQS) for pipeline stages
2. Implement stateless workers for rendering
3. Add worker isolation (containerized rendering)
4. Support multiple product niches with separate configs
5. Add batch processing for high-volume product intake
6. Performance optimization and load testing
7. Set up monitoring + alerting (Prometheus/Grafana or CloudWatch)
8. Complete incident response runbooks

#### Code Modules
- `app/services/queue.py`
- `app/services/worker_pool.py`
- `infra/docker-compose.yml`
- `infra/Dockerfile`
- `infra/terraform/` (if cloud)

#### Tests
- `tests/integration/test_queue_flow.py`
- `tests/integration/test_worker_isolation.py`
- Load tests

#### Docs to Generate
- `docs/phases/phase-05-scale.md`
- `docs/security/threat-model.md`
- `docs/security/incident-runbooks.md`
- `docs/ops/daily-runbook.md`
- `docs/ops/weekly-review.md`
- `docs/adrs/ADR-0003-queue-selection.md`
- `docs/adrs/ADR-0004-storage-architecture.md`

#### Exit Criteria
- Pipeline handles 100+ products/day without degradation
- Workers are isolated and stateless
- Queue-based processing decouples pipeline stages
- Multi-niche configuration works without code changes
- Monitoring dashboards operational
- Incident runbooks tested via tabletop exercises

#### Risks & Rollback
| Risk | Mitigation | Rollback |
|------|-----------|----------|
| Queue complexity | Start with Redis Streams, upgrade if needed | Fall back to synchronous processing |
| Cost scaling | Budget alerts, auto-pause at threshold | Reduce batch size |
| Multi-niche conflicts | Namespace isolation | Process niches sequentially |

---

## APPENDIX A — CONTROL MATRIX (from Agents_Security.md)

| Threat | Control | Implementation | Status |
|--------|---------|----------------|--------|
| Secrets theft | Secrets Manager + RBAC | `app/services/secrets.py` | Phase 1 |
| Malicious prompts | Input validation + sanitization | `InputValidator` class | Phase 1 |
| Unauthorized publishing | QA gate + compliance_status check | `qa_checker.py` + flow guards | Phase 1 |
| Media tampering | Content hash + signed URLs | `content_hasher.py`, `media_signer.py` | Phase 3 |
| Account compromise | Token rotation + incident runbook | `incident_manager.py` | Phase 3 |
| API abuse | Rate limiting + circuit breakers | `rate_limits.py` + adapter-level | Phase 3 |
| DMCA notice | Immediate takedown procedure | Incident runbook | Phase 5 |
| Duplicate spam | Hash-based dedup + similarity check | `content_hasher.py`, `anti_repetition.py` | Phase 3 |
| Audit tampering | Append-only log + hash chain | `audit_logger.py` | Phase 1 |

## APPENDIX B — IMPLEMENTATION CHECKLIST (from Agents_Security.md)

- [ ] Threat model documented
- [ ] RBAC roles defined and enforced
- [ ] Secrets manager integrated (no hardcoded creds)
- [ ] Signed URLs for all media access
- [ ] Immutable audit logs with hash chain
- [ ] Rate limiting per platform
- [ ] Circuit breakers on all external APIs
- [ ] Input validation on all external text
- [ ] Prompt injection filtering
- [ ] Dependency scanning in CI/CD
- [ ] Test environment isolated from production
- [ ] DMCA incident runbook tested
- [ ] Token leak incident runbook tested
- [ ] Account restriction incident runbook tested
- [ ] Affiliate disclosure compliance verified per platform

## APPENDIX C — INCIDENT RESPONSE CHECKLIST

- [ ] **Detection**: Alert fired or manual report received
- [ ] **Triage**: Severity assigned (P1/P2/P3)
- [ ] **Containment**: Affected content taken down, credentials rotated if needed
- [ ] **Investigation**: Audit trail reviewed, root cause identified
- [ ] **Resolution**: Fix applied, guardrails updated
- [ ] **Post-mortem**: Incident report written, learnings applied
- [ ] **Prevention**: Policies/rules updated to prevent recurrence
