"""orchestration.crew — CrewAI agent and task definitions."""

from __future__ import annotations

from crewai import Agent, Task, Crew, Process


def build_research_planner() -> Agent:
    return Agent(
        role="Research Planner",
        goal="Define scope, sampling budgets, queries, and collection plan",
        backstory=(
            "You are a senior media strategist. You determine which platforms, "
            "keywords, and budgets to use for competitive ad research."
        ),
        verbose=True,
        allow_delegation=False,
    )


def build_collector_agent(platform: str) -> Agent:
    return Agent(
        role=f"{platform.title()} Collector",
        goal=f"Collect public ads from {platform} via approved APIs",
        backstory=(
            f"You collect ad creatives from {platform} using Apify actors "
            "or official APIs. You never bypass authentication or anti-bot protections."
        ),
        verbose=True,
        allow_delegation=False,
    )


def build_media_analyzer() -> Agent:
    return Agent(
        role="Media Analyzer",
        goal="Extract deterministic tags from ad creatives using vision or heuristic rules",
        backstory=(
            "You analyze ad images/videos and produce structured tags "
            "(format, hook, angle, offer, proof, CTA, risk) using an enum-only taxonomy."
        ),
        verbose=True,
        allow_delegation=False,
    )


def build_comment_miner() -> Agent:
    return Agent(
        role="Comment Miner",
        goal="Extract anonymized themes from ad comments without storing PII",
        backstory=(
            "You process raw comments to find questions, objections, and desire language. "
            "You never store raw comments or personal identifiers."
        ),
        verbose=True,
        allow_delegation=False,
    )


def build_synthesizer() -> Agent:
    return Agent(
        role="Synthesizer",
        goal="Cluster winners, extract patterns, and write AoT atoms",
        backstory=(
            "You rank ads by engagement+recency, cluster by format/angle/hook/offer, "
            "and produce evidence-backed insights with Atom-of-Thought reasoning."
        ),
        verbose=True,
        allow_delegation=False,
    )


def build_brief_writer() -> Agent:
    return Agent(
        role="Brief Writer",
        goal="Generate a complete creative brief from insights and brand bible",
        backstory=(
            "You write performance creative briefs with SMP, RTBs, hooks, scripts, "
            "and a testing matrix. Every claim traces to asset evidence."
        ),
        verbose=True,
        allow_delegation=False,
    )


def build_qa_agent() -> Agent:
    return Agent(
        role="QA Gate",
        goal="Validate brief for PII, copy overlap, and claim risks — block export on FAIL",
        backstory=(
            "You enforce compliance: no PII, no verbatim competitor copy, "
            "no unsupported medical/financial claims. FAIL blocks export."
        ),
        verbose=True,
        allow_delegation=False,
    )


def build_exporter() -> Agent:
    return Agent(
        role="Exporter",
        goal="Package approved deliverables as JSON, Markdown, and optional zip",
        backstory="You export final approved briefs and artifacts, excluding raw comments.",
        verbose=True,
        allow_delegation=False,
    )


# ── Task builders ─────────────────────────────────


def task_plan(agent: Agent, workspace_id: str) -> Task:
    return Task(
        description=f"Create collection plan for workspace '{workspace_id}'",
        expected_output="plan.json with platforms, keywords, budgets",
        agent=agent,
    )


def task_collect(agent: Agent, platform: str) -> Task:
    return Task(
        description=f"Collect ads from {platform} per plan budgets",
        expected_output="assets.json + raw_refs.json",
        agent=agent,
    )


def task_analyze(agent: Agent) -> Task:
    return Task(
        description="Tag all collected assets (vision or heuristic fallback)",
        expected_output="tags.json for all assets",
        agent=agent,
    )


def task_mine_comments(agent: Agent) -> Task:
    return Task(
        description="Extract anonymized comment themes from available data",
        expected_output="comment_themes.json (no raw comments stored)",
        agent=agent,
    )


def task_synthesize(agent: Agent) -> Task:
    return Task(
        description="Rank, cluster, generate insights, and write AoT ledger",
        expected_output="clusters.json + insights.md + aot_ledger.jsonl",
        agent=agent,
    )


def task_write_brief(agent: Agent) -> Task:
    return Task(
        description="Generate creative brief from insights + brand bible",
        expected_output="brief.md + brief.json",
        agent=agent,
    )


def task_qa(agent: Agent) -> Task:
    return Task(
        description="Run PII, copy, and claim checks on brief",
        expected_output="qa_report.json + qa_report.md",
        agent=agent,
    )


def task_export(agent: Agent) -> Task:
    return Task(
        description="Export approved deliverables to run directory",
        expected_output="JSON bundle + brief.md + optional zip",
        agent=agent,
    )


def build_crew(workspace_id: str) -> Crew:
    """Assemble the full CrewAI crew for a pipeline run."""
    planner = build_research_planner()
    tiktok_col = build_collector_agent("tiktok")
    meta_col = build_collector_agent("meta")
    x_col = build_collector_agent("x")
    pinterest_col = build_collector_agent("pinterest")
    analyzer = build_media_analyzer()
    miner = build_comment_miner()
    synth = build_synthesizer()
    writer = build_brief_writer()
    qa = build_qa_agent()
    exporter = build_exporter()

    tasks = [
        task_plan(planner, workspace_id),
        task_collect(tiktok_col, "tiktok"),
        task_collect(meta_col, "meta"),
        task_collect(x_col, "x"),
        task_collect(pinterest_col, "pinterest"),
        task_analyze(analyzer),
        task_mine_comments(miner),
        task_synthesize(synth),
        task_write_brief(writer),
        task_qa(qa),
        task_export(exporter),
    ]

    return Crew(
        agents=[
            planner, tiktok_col, meta_col, x_col, pinterest_col,
            analyzer, miner, synth, writer, qa, exporter,
        ],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
