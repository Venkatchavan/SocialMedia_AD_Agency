"""cli — Command-line interface for the Creative Intelligence OS."""

from __future__ import annotations

import argparse
import sys

from rich.console import Console

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="creative-os",
        description="Creative Intelligence OS — Ad Research Pipeline",
    )
    sub = parser.add_subparsers(dest="command")

    # run command
    run_p = sub.add_parser("run", help="Run a full pipeline for a workspace")
    run_p.add_argument("--workspace", "-w", default="sample_client", help="Workspace ID")
    run_p.add_argument("--csv", help="Optional CSV path for manual import")

    # schedule command
    sched_p = sub.add_parser("schedule", help="Start the weekly scheduler loop")
    sched_p.add_argument("--once", action="store_true", help="Run one cycle and exit")

    # check command
    sub.add_parser("check", help="Run line-count enforcement check")

    # crew command
    crew_p = sub.add_parser("crew", help="Run pipeline via CrewAI agents")
    crew_p.add_argument("--workspace", "-w", default="sample_client")

    # collect command
    coll_p = sub.add_parser("collect", help="Collect live ads from TikTok/Meta via Apify")
    coll_p.add_argument("--workspace", "-w", default="sample_client")
    coll_p.add_argument("--platform", choices=["tiktok", "meta", "pinterest"], default="tiktok")
    coll_p.add_argument("--brand", default="tech")
    coll_p.add_argument("--keywords", help="Comma-separated keywords", default="")
    coll_p.add_argument("--count", type=int, default=10, help="Results per keyword")
    coll_p.add_argument("--run", action="store_true", help="Run full pipeline after collecting")

    # preflight command
    pre_p = sub.add_parser("preflight", help="Run compliance pre-run checklist for a workspace")
    pre_p.add_argument("--workspace", "-w", default="sample_client")

    # cleanup command
    clean_p = sub.add_parser("cleanup", help="Purge expired runs per retention policy")
    clean_p.add_argument("--workspace", "-w", default=None, help="Specific workspace (omit = all)")
    clean_p.add_argument("--dry-run", action="store_true", help="Preview without deleting")

    # incident command
    inc_p = sub.add_parser("incident", help="Trigger incident response for a run")
    inc_p.add_argument("--workspace", "-w", required=True)
    inc_p.add_argument("--run-id", required=True)
    inc_p.add_argument("--type", default="other",
                       choices=["pii_leaked", "unauthorized_collection",
                                "competitor_copy_exported", "bypass_instruction_detected",
                                "cross_workspace_contamination", "other"])
    inc_p.add_argument("--description", default="Manual incident trigger")
    inc_p.add_argument("--rotate-keys", action="store_true")

    args = parser.parse_args()

    if args.command == "run":
        _cmd_run(args.workspace, args.csv)
    elif args.command == "collect":
        _cmd_collect(args.workspace, args.platform, args.brand, args.keywords, args.count, args.run)
    elif args.command == "schedule":
        _cmd_schedule(getattr(args, "once", False))
    elif args.command == "check":
        _cmd_check()
    elif args.command == "crew":
        _cmd_crew(args.workspace)
    elif args.command == "preflight":
        _cmd_preflight(args.workspace)
    elif args.command == "cleanup":
        _cmd_cleanup(args.workspace, dry_run=args.dry_run)
    elif args.command == "incident":
        _cmd_incident(args.workspace, args.run_id, args.type, args.description, args.rotate_keys)
    else:
        parser.print_help()


def _cmd_run(workspace_id: str, csv_path: str | None) -> None:
    from orchestration.pipeline import run_pipeline
    from core.schemas_asset import Asset

    console.print(f"[bold green]Running pipeline for workspace: {workspace_id}[/]")

    assets: list[Asset] = []
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


def _cmd_collect(
    workspace_id: str,
    platform: str,
    brand: str,
    keywords_str: str,
    count: int,
    run_after: bool,
) -> None:
    from core.utils_time import utcnow_iso
    import re
    run_id = re.sub(r"[^0-9_]", "", utcnow_iso()[:16].replace("T", "_").replace(":", ""))
    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]

    console.print(f"[bold blue]Collecting {platform.upper()} ads[/] brand=[cyan]{brand}[/] keywords={keywords} count={count}")

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
                workspace_id, run_id, brand,
                ad_library_urls=keywords,
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


def _cmd_schedule(once: bool = False) -> None:
    console.print("[bold blue]Starting scheduler...[/]")
    if once:
        from orchestration.scheduler import run_scheduled_cycle
        run_scheduled_cycle()
        console.print("[bold green]Scheduler cycle complete.[/]")
    else:
        from orchestration.scheduler import run_scheduler_loop
        console.print("[bold blue]Starting scheduler loop (weekly cadence)...[/]")
        run_scheduler_loop()


def _cmd_check() -> None:
    from scripts.check_linecount import check_linecount
    from pathlib import Path

    root = Path(__file__).resolve().parent
    violations = check_linecount(root)
    if violations:
        console.print(f"[bold red]FAIL: {len(violations)} file(s) exceed 250 lines[/]")
        for path, count in violations:
            console.print(f"  {path}: {count} lines")
        sys.exit(1)
    console.print("[bold green]PASS: All files ≤250 lines[/]")


def _cmd_crew(workspace_id: str) -> None:
    from orchestration.crew import _get_llm
    console.print(f"[bold blue]Running CrewAI pipeline for: {workspace_id}[/]")
    llm = _get_llm()
    if not llm:
        console.print(
            "[yellow]No LLM API key found.[/] CrewAI agents require an LLM to run tasks.\n"
            "Set one of these in your [bold].env[/] file:\n"
            "  [cyan]OPENAI_API_KEY=sk-...[/]\n"
            "  [cyan]GEMINI_API_KEY=...[/]\n\n"
            "[dim]The direct pipeline (`python cli.py run`) works without an LLM key.[/dim]"
        )
        return
    try:
        from orchestration.crew import build_crew
        crew = build_crew(workspace_id)
        result = crew.kickoff()
        console.print(f"[bold green]Crew result:[/] {result}")
    except Exception as exc:
        console.print(f"[bold red]Crew error:[/] {exc}")
        sys.exit(1)


def _cmd_preflight(workspace_id: str) -> None:
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


def _cmd_cleanup(workspace_id: str | None, *, dry_run: bool = False) -> None:
    from compliance.cleanup import purge_expired_runs, purge_all_workspaces
    tag = "[dim][DRY RUN][/dim] " if dry_run else ""
    if workspace_id:
        console.print(f"{tag}[bold blue]Running cleanup for workspace: {workspace_id}[/]")
        report = purge_expired_runs(workspace_id, dry_run=dry_run)
        reports = [report]
    else:
        console.print(f"{tag}[bold blue]Running cleanup for ALL workspaces[/]")
        reports = purge_all_workspaces(dry_run=dry_run)
    for r in reports:
        mb = r.bytes_freed / 1_048_576
        console.print(
            f"  [cyan]{r.workspace_id}[/]: {r.total_runs_purged} run(s) purged, "
            f"{len(r.sensitive_files_removed)} sensitive file(s) removed, "
            f"{mb:.2f} MB freed"
        )
        for err in r.errors:
            console.print(f"    [red]Error:[/] {err}")
    console.print("[bold green]✓ Cleanup complete[/]")


def _cmd_incident(
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


if __name__ == "__main__":
    main()
