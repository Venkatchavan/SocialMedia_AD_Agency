"""cli — Command-line interface for the Creative Intelligence OS."""

from __future__ import annotations

import argparse

from rich.console import Console

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="creative-os",
        description="Creative Intelligence OS — Ad Research Pipeline",
    )
    sub = parser.add_subparsers(dest="command")

    # run
    run_p = sub.add_parser("run", help="Run a full pipeline for a workspace")
    run_p.add_argument("--workspace", "-w", default="sample_client")
    run_p.add_argument("--csv", help="Optional CSV path for manual import")

    # collect
    coll_p = sub.add_parser("collect", help="Collect live ads from TikTok/Meta via Apify")
    coll_p.add_argument("--workspace", "-w", default="sample_client")
    coll_p.add_argument("--platform", choices=["tiktok", "meta", "pinterest"], default="tiktok")
    coll_p.add_argument("--brand", default="tech")
    coll_p.add_argument("--keywords", default="", help="Comma-separated keywords")
    coll_p.add_argument("--count", type=int, default=10, help="Results per keyword")
    coll_p.add_argument("--run", action="store_true", help="Run full pipeline after collecting")

    # schedule
    sched_p = sub.add_parser("schedule", help="Start the weekly scheduler loop")
    sched_p.add_argument("--once", action="store_true", help="Run one cycle and exit")

    # check
    sub.add_parser("check", help="Run line-count enforcement check")

    # crew
    crew_p = sub.add_parser("crew", help="Run pipeline via CrewAI agents")
    crew_p.add_argument("--workspace", "-w", default="sample_client")

    # preflight
    pre_p = sub.add_parser("preflight", help="Run compliance pre-run checklist")
    pre_p.add_argument("--workspace", "-w", default="sample_client")

    # cleanup
    clean_p = sub.add_parser("cleanup", help="Purge expired runs per retention policy")
    clean_p.add_argument("--workspace", "-w", default=None)
    clean_p.add_argument("--dry-run", action="store_true")

    # incident
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
    from cli_commands import (
        cmd_check, cmd_cleanup, cmd_collect, cmd_crew,
        cmd_incident, cmd_preflight, cmd_run, cmd_schedule,
    )

    if args.command == "run":
        cmd_run(args.workspace, args.csv)
    elif args.command == "collect":
        cmd_collect(args.workspace, args.platform, args.brand,
                    args.keywords, args.count, args.run)
    elif args.command == "schedule":
        cmd_schedule(getattr(args, "once", False))
    elif args.command == "check":
        cmd_check()
    elif args.command == "crew":
        cmd_crew(args.workspace)
    elif args.command == "preflight":
        cmd_preflight(args.workspace)
    elif args.command == "cleanup":
        cmd_cleanup(args.workspace, dry_run=args.dry_run)
    elif args.command == "incident":
        cmd_incident(args.workspace, args.run_id, args.type,
                     args.description, args.rotate_keys)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
