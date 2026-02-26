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

    args = parser.parse_args()

    if args.command == "run":
        _cmd_run(args.workspace, args.csv)
    elif args.command == "schedule":
        _cmd_schedule(getattr(args, "once", False))
    elif args.command == "check":
        _cmd_check()
    elif args.command == "crew":
        _cmd_crew(args.workspace)
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
    import os
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


if __name__ == "__main__":
    main()
