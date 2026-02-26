"""cli_commands — Implementation of each CLI sub-command."""

from __future__ import annotations

import re
import sys

from rich.console import Console

console = Console()


def cmd_run(workspace_id: str, csv_path: str | None) -> None:
    from orchestration.pipeline import run_pipeline
    from core.schemas_asset import Asset  # noqa: F401

    console.print(f"[bold green]Running pipeline for workspace: {workspace_id}[/]")
    assets = []
    if csv_path:
        from collectors.csv_importer import import_csv
        assets = import_csv(csv_path, workspace_id, "manual", "imported")
    if not assets:
        console.print("[yellow]No assets provided. Use --csv or configure collectors.[/]")
        console.print("[dim]Running with empty asset list for demo...[/dim]")
    try:
        result = run_pipeline(workspace_id, assets)
        console.print(f"[bold green]✓ Pipeline completed:[/] {result}")
    except Exception as exc:
        console.print(f"[bold red]✗ Pipeline failed:[/] {exc}")
        sys.exit(1)


def cmd_collect(
    workspace_id: str,
    platform: str,
    brand: str,
    keywords_str: str,
    count: int,
    run_after: bool,
) -> None:
    from core.utils_time import utcnow_iso
    run_id = re.sub(r"[^0-9_]", "", utcnow_iso()[:16].replace("T", "_").replace(":", ""))
    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
    console.print(
        f"[bold blue]Collecting {platform.upper()} ads[/] "
        f"brand=[cyan]{brand}[/] keywords={keywords} count={count}"
    )
    assets = []
    try:
        if platform == "tiktok":
            from collectors.tiktok_collector import TikTokCollector
            assets = TikTokCollector().collect(
                workspace_id, run_id, brand,
                keywords=keywords, count_per_keyword=count,
            )
        elif platform == "meta":
            from collectors.meta_collector import MetaCollector
            assets = MetaCollector().collect(
                workspace_id, run_id, brand, ad_library_urls=keywords,
            )
        elif platform == "pinterest":
            from collectors.pinterest_collector import PinterestCollector
            assets = PinterestCollector().collect(
                workspace_id, run_id, brand,
                keywords=keywords, count_per_keyword=count,
            )
    except Exception as exc:
        console.print(f"[bold red]✗ Collection failed:[/] {exc}")
        sys.exit(1)

    console.print(f"[bold green]✓ Collected {len(assets)} assets[/]")
    for a in assets[:5]:
        console.print(f"  [dim]{a.asset_id}[/] — {(a.caption_or_copy or a.headline or '')[:80]}")
    if len(assets) > 5:
        console.print(f"  [dim]... and {len(assets) - 5} more[/]")
    if run_after and assets:
        console.print("\n[bold blue]Running pipeline on collected assets...[/]")
        from orchestration.pipeline import run_pipeline
        result = run_pipeline(workspace_id, assets)
        console.print(f"[bold green]✓ Pipeline completed:[/] {result}")


def cmd_schedule(once: bool = False) -> None:
    console.print("[bold blue]Starting scheduler...[/]")
    if once:
        from orchestration.scheduler import run_scheduled_cycle
        run_scheduled_cycle()
        console.print("[bold green]Scheduler cycle complete.[/]")
    else:
        from orchestration.scheduler import run_scheduler_loop
        console.print("[bold blue]Starting scheduler loop (weekly cadence)...[/]")
        run_scheduler_loop()


def cmd_check() -> None:
    from scripts.check_linecount import check_linecount
    from pathlib import Path
    root = Path(__file__).resolve().parent
    violations = check_linecount(root)
    if violations:
        console.print(f"[bold red]FAIL: {len(violations)} file(s) exceed 250 lines[/]")
        for path, cnt in violations:
            console.print(f"  {path}: {cnt} lines")
        sys.exit(1)
    console.print("[bold green]PASS: All files ≤250 lines[/]")


def cmd_crew(workspace_id: str) -> None:
    from orchestration.crew import _get_llm
    console.print(f"[bold blue]Running CrewAI pipeline for: {workspace_id}[/]")
    llm = _get_llm()
    if not llm:
        console.print(
            "[yellow]No LLM API key found.[/] Set OPENAI_API_KEY or GEMINI_API_KEY in .env\n"
            "[dim]The direct pipeline (`python cli.py run`) works without an LLM key.[/dim]"
        )
        return
    try:
        from orchestration.crew import build_crew
        result = build_crew(workspace_id).kickoff()
        console.print(f"[bold green]Crew result:[/] {result}")
    except Exception as exc:
        console.print(f"[bold red]Crew error:[/] {exc}")
        sys.exit(1)


def cmd_preflight(workspace_id: str) -> None:
    from compliance.preflight import run_preflight
    console.print(f"[bold blue]Running preflight for workspace: {workspace_id}[/]")
    report = run_preflight(workspace_id, raise_on_error=False)
    for w in report.warnings:
        console.print(f"  [yellow]WARN[/]  {w}")
    for e in report.errors:
        console.print(f"  [bold red]ERROR[/] {e}")
    if report.passed:
        console.print("[bold green]✓ Preflight PASS[/]")
    else:
        console.print("[bold red]✗ Preflight FAIL[/] — fix errors before running pipeline")
        sys.exit(1)


def cmd_cleanup(workspace_id: str | None, *, dry_run: bool = False) -> None:
    from compliance.cleanup import purge_expired_runs, purge_all_workspaces
    tag = "[dim][DRY RUN][/dim] " if dry_run else ""
    if workspace_id:
        console.print(f"{tag}[bold blue]Running cleanup for workspace: {workspace_id}[/]")
        reports = [purge_expired_runs(workspace_id, dry_run=dry_run)]
    else:
        console.print(f"{tag}[bold blue]Running cleanup for ALL workspaces[/]")
        reports = purge_all_workspaces(dry_run=dry_run)
    for r in reports:
        mb = r.bytes_freed / 1_048_576
        console.print(
            f"  [cyan]{r.workspace_id}[/]: {r.total_runs_purged} run(s) purged, "
            f"{len(r.sensitive_files_removed)} sensitive file(s) removed, {mb:.2f} MB freed"
        )
        for err in r.errors:
            console.print(f"    [red]Error:[/] {err}")
    console.print("[bold green]✓ Cleanup complete[/]")


def cmd_incident(
    workspace_id: str,
    run_id: str,
    incident_type: str,
    description: str,
    rotate_keys: bool,
) -> None:
    from compliance.incident import trigger_incident
    console.print(f"[bold red]⚠ Triggering incident response[/] workspace={workspace_id} run={run_id}")
    incident = trigger_incident(
        run_id=run_id,
        workspace_id=workspace_id,
        incident_type=incident_type,
        description=description,
        key_rotation_required=rotate_keys,
    )
    for action in incident.actions_taken:
        console.print(f"  [green]✓[/] {action}")
    if incident.key_rotation_required:
        console.print("[bold yellow]⚠ Rotate your API keys in .env immediately.[/]")
    console.print(f"[bold green]✓ Incident logged[/] ({len(incident.data_purged)} files purged)")


def cmd_enhance_brand(
    workspace_id: str,
    keywords_str: str = "",
    hashtags_str: str = "",
    extra_context: str = "",
    run_id: str | None = None,
    list_versions: bool = False,
) -> None:
    from brand_enchancement.engine import update_brand_bible
    from brand_enchancement.versioning import list_versions as _list_versions

    if list_versions:
        versions = _list_versions(workspace_id)
        if not versions:
            console.print(f"[yellow]No brand bible versions found for workspace: {workspace_id}[/]")
            return
        console.print(f"[bold blue]Brand bible versions for: {workspace_id}[/]")
        for v in versions:
            console.print(
                f"  [cyan]v{v['version']}[/] | run={v['run_id'][:20]} | {v['updated_at'][:16]}"
            )
        return

    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
    hashtags = [h.strip() for h in hashtags_str.split(",") if h.strip()]

    console.print(
        f"[bold blue]Enhancing brand bible[/] workspace=[cyan]{workspace_id}[/] "
        f"kw={keywords} ht={hashtags}"
    )
    try:
        result = update_brand_bible(
            workspace_id=workspace_id,
            keywords=keywords,
            hashtags=hashtags,
            extra_context=extra_context,
            run_id=run_id,
        )
        console.print(f"[bold green]✓ Brand bible updated → v{result.version}[/]")
        for line in result.report.splitlines()[1:]:
            console.print(f"  [dim]{line}[/dim]")
    except Exception as exc:
        console.print(f"[bold red]✗ Brand enhancement failed:[/] {exc}")
        sys.exit(1)
