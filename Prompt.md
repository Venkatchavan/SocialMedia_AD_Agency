You are a senior AI systems architect + growth automation engineer.

Design a production-grade CrewAI system for a SOLO founder running an AI-powered affiliate ad agency for Amazon products.

PRIMARY PIPELINE (must be the backbone of the architecture)
Amazon Product -> Reference Intelligence (movie/anime/music/novel) -> Rights/Licensing Validation -> Creative Generation (image/video/caption) -> Platform Adaptation -> Publishing -> Analytics -> Optimization Loop

IMPORTANT INTERPRETATION OF "REFERENCE"
A "reference" can be:
1) a direct licensed reference (licensed franchise visual/audio/text usage),
2) a public-domain reference,
3) a style/theme/trope reference (no copyrighted asset reuse),
4) a commentary/review reference (where legally safe and clearly documented).

The system MUST distinguish these types and enforce different rules for each.

NON-NEGOTIABLE SYSTEM REQUIREMENTS
- Scalable architecture (queue-based, stateless workers where possible)
- Clean codebase (modular, testable, documented)
- Agentic rules that prevent illegal actions
- Strong security (secret management, RBAC, audit logs, signed URLs, least privilege)
- Compliance-first workflow (rights + affiliate + platform policy checks)
- Phase-by-phase documentation generation
- Tool-by-tool and agent-by-agent docs generated automatically after implementation milestones

GOAL
Build a CrewAI-based end-to-end content pipeline that:
1) pulls or ingests Amazon product candidates,
2) finds culturally relevant references (movie/anime/music/novel) for the product niche,
3) validates rights and allowed usage,
4) generates images/videos/scripts/captions from approved references,
5) posts to TikTok, Instagram, X, Pinterest,
6) tracks performance + affiliate outcomes,
7) runs experiments and optimizes content angles.

OUTPUT FORMAT
Return the complete solution in 14 sections:

SECTION 1 — SYSTEM OVERVIEW
- Explain the entire pipeline from product intake to optimization
- ASCII architecture diagram
- Which components are agents vs deterministic services
- Data flow and control flow

SECTION 2 — CREWAI ORCHESTRATION DESIGN
- CrewAI Crews, Agents, Tasks, Flows, State, Memory
- Event-driven flow branches:
  APPROVE -> RENDER -> QA -> PUBLISH
  REWRITE -> back to script/prompt generation
  REJECT -> archive with reason
- Human approval checkpoints (optional but supported)
- Retry/recovery rules

SECTION 3 — AGENT LIST (DETAILED)
Define at least these agents with role, goal, tools, inputs, outputs, guardrails, KPIs, fail conditions, handoff rules:
1. Product Intake Agent
2. Product Enrichment Agent
3. Reference Intelligence Agent (movie/anime/music/novel mapping)
4. Rights & License Verification Agent
5. Reference Risk Scoring Agent
6. Creative Strategy Agent
7. Scriptwriter Agent
8. Storyboard / Visual Prompt Agent
9. Asset Generation Coordinator Agent
10. Video Assembly Agent
11. Caption + SEO + Disclosure Agent
12. Platform Adaptation Agent
13. QA & Policy Checker Agent
14. Publisher / Scheduler Agent
15. Analytics & Experimentation Agent
16. Orchestrator / Manager Agent

SECTION 4 — AGENTIC RULES (LEGAL/SAFE)
Create a strict “Agent Constitution” that every agent must follow:
- No use of unlicensed copyrighted assets
- No scraping or automation that violates platform ToS
- No deceptive affiliate disclosures
- No fake claims/testimonials
- No impersonation/brand confusion
- No credential exposure
- No publishing without compliance approval
- No bypassing audit logs
Define allowed actions, forbidden actions, and escalation rules.

SECTION 5 — SECURITY ARCHITECTURE
Design a secure architecture with:
- Secrets manager usage
- Role-based access control (RBAC)
- API key scope separation by platform
- Signed URLs for media assets
- Hash-based asset tracking and dedupe
- Immutable audit logs
- Worker isolation for rendering
- Input validation / prompt injection defenses
- Rate limiting / abuse controls
- Incident response plan (DMCA, account restriction, token leak)

SECTION 6 — CLEAN CODE ARCHITECTURE
Provide a maintainable project structure:
- app/
- agents/
- flows/
- services/
- adapters/
- policies/
- schemas/
- tests/
- docs/
- infra/
Use clear interfaces and dependency boundaries.
Specify coding standards:
- type hints
- linting
- unit + integration tests
- structured logging
- config via environment + typed settings
- no business logic inside agent prompt strings

SECTION 7 — REFERENCE INTELLIGENCE ENGINE (KEY PART)
Design how the system maps products to cultural references:
- Product -> category -> use-case -> audience persona -> “reference graph”
- Reference graph includes:
  * title/work/franchise
  * medium (anime/movie/music/novel)
  * reference type (licensed/direct, public domain, style-only, commentary)
  * allowed usage mode
  * risk score
  * source metadata
- Include a “Reference Prompt Compiler” that converts approved references into generation-safe prompts
- Include fallbacks when no safe direct references exist (style/trope mode)

SECTION 8 — RIGHTS / LICENSING COMPLIANCE ENGINE
Design a deterministic subsystem with:
- rights_registry schema
- asset provenance checks
- license proof requirements
- expiry checks
- usage-scope checks (commercial? social? derivative allowed?)
- trademark/character likeness checks
- auto-block thresholds using risk score (0–100)
- approve/rewrite/reject outputs
- audit trail for every decision

SECTION 9 — CONTENT GENERATION ENGINE
Define:
- script templates by content angle (comparison, top-3, story, problem-solution, aesthetic, meme-style)
- scene templates
- visual prompt templates
- video generation workflow
- voiceover workflow
- caption generation workflow with SEO + disclosures
- anti-repetition logic (hashing, semantic similarity threshold)
- content quality scoring before publish

SECTION 10 — PLATFORM PUBLISHING LAYER
For TikTok, Instagram, X, Pinterest:
- account/app prerequisites
- posting APIs / adapter design
- media processing states
- scheduling + retry logic
- platform-specific caption formatting
- error taxonomy (AUTH, RATE_LIMIT, VALIDATION, POLICY, TRANSIENT)
- fallback to manual queue when API posting unavailable
- platform capability matrix

SECTION 11 — ANALYTICS & EXPERIMENTATION
Define:
- event tracking model (impressions, clicks, saves, watch time proxies, CTR)
- affiliate attribution tracking inputs
- experiment framework (hook A/B, reference type A/B, caption A/B, posting-time A/B)
- optimization loop (what gets promoted, paused, rewritten)
- Reddit-derived hypotheses as experimental priors (not facts)

SECTION 12 — DATA MODELS / SCHEMAS
Design schemas (SQL + JSON examples) for:
- products
- references
- rights_registry
- content_briefs
- scripts
- asset_manifest
- post_queue
- published_posts
- performance_metrics
- experiments
- incidents
- audit_events

SECTION 13 — DOCUMENTATION GENERATION PLAN (MANDATORY)
After each phase, tool, and agent implementation, generate docs automatically:
A) Phase docs (goal, scope, architecture, decisions, risks, next steps)
B) Agent docs (purpose, prompt, tools, I/O contracts, guardrails, examples)
C) Tool docs (API contracts, auth, rate limits, failure modes)
D) Flow docs (states, branches, retries, rollback)
E) Security docs (threat model, controls, incident runbook)
F) Compliance docs (rights checks, disclosures, audit process)
G) Ops docs (daily runbook, weekly review, on-call incidents)
H) ADRs (Architecture Decision Records)
Provide the docs folder structure and templates.

SECTION 14 — IMPLEMENTATION ROADMAP
Phase 1 (MVP): Product -> Script -> Caption -> Manual Publish
Phase 2: Add reference engine + rights registry
Phase 3: Add video rendering + API publishing
Phase 4: Add analytics + experimentation
Phase 5: Scale (queues, workers, multi-niche)
Each phase must include:
- tasks
- code modules
- tests
- docs to generate
- exit criteria
- risks and rollback plan

IMPORTANT OUTPUT RULES
- Be brutally practical and implementation-oriented.
- Compliance-critical decisions must be deterministic, not agent opinion only.
- All publishing must require QA+Compliance approval.
- Separate “creative generation” from “rights validation”.
- Assume API-first integrations; no illegal automation.
- Include sample prompts for each agent, especially:
  Reference Intelligence Agent
  Rights & License Verification Agent
  Scriptwriter Agent
  Caption + Disclosure Agent
  Publisher Agent
- Include examples of APPROVE / REWRITE / REJECT decision outputs.