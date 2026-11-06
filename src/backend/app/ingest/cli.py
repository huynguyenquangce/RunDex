"""Command line entry point: python -m app.ingest <command>."""

import argparse
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
from sqlalchemy import select

from app.db import SessionLocal
from app.ingest.fetch_service import fetch_source, is_due, pages_waiting_for_extraction
from app.ingest.fetcher import USER_AGENT, Fetcher
from app.ingest.pipeline import approve, event_name_for, pending_proposals, process_outbox, reject
from app.ingest.sources import DEFAULT_SOURCES_PATH, load_sources, sync_sources
from app.models import Source


def _cmd_sources_sync(args: argparse.Namespace) -> int:
    configs = load_sources(Path(args.file))
    with SessionLocal() as session:
        created, updated = sync_sources(session, configs)
    print(f"sources: {created} created, {updated} updated ({len(configs)} in {args.file})")
    return 0


def _cmd_sources_list(_: argparse.Namespace) -> int:
    with SessionLocal() as session:
        for source in session.scalars(select(Source).order_by(Source.tier, Source.id)):
            state = "on " if source.enabled else "off"
            print(f"{state} T{source.tier} {source.kind:<12} {source.id:<24} {source.url}")
    return 0


def _run_fetch(source: str | None, limit: int, delay: float, force: bool) -> None:
    now = datetime.now(UTC)
    with (
        SessionLocal() as session,
        httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=20.0, follow_redirects=True
        ) as client,
    ):
        fetcher = Fetcher(client, delay_seconds=delay)
        query = select(Source).where(Source.enabled).order_by(Source.tier, Source.id)
        if source:
            query = query.where(Source.id == source)
        sources = [s for s in session.scalars(query) if force or is_due(s, now)]
        if not sources:
            print("fetch: nothing due (use --force to fetch anyway)")
        for src in sources:
            report = fetch_source(session, src, fetcher, limit=limit, now=now)
            print(
                f"fetch: {src.id:<24} discovered={report.discovered} "
                f"new_or_changed={report.new_or_changed} unchanged={report.unchanged} "
                f"skipped={len(report.skipped)}"
            )
            for line in report.skipped[:3]:
                print(f"    skipped: {line}")


def _cmd_fetch(args: argparse.Namespace) -> int:
    _run_fetch(args.source, args.limit, args.delay, args.force)
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    """One pass of the whole pipeline: sync sources, fetch, apply what the extractor produced."""
    with SessionLocal() as session:
        created, updated = sync_sources(session, load_sources(DEFAULT_SOURCES_PATH))
        print(f"sources: {created} created, {updated} updated")
    _run_fetch(None, args.limit, args.delay, args.force)
    waiting = pages_waiting_for_extraction()
    _cmd_apply(args)
    if waiting:
        print(
            f"extract: {len(waiting)} fetched page(s) wait for the extractor. Ask Claude Code to "
            "run the event-extractor agent on data/inbox, then run `run` again (or `apply`)."
        )
    with SessionLocal() as session:
        print(f"review: {len(pending_proposals(session))} proposal(s) waiting for a decision")
    return 0


def _cmd_worker(args: argparse.Namespace) -> int:
    """Run `run` forever, every N hours. Stop with Ctrl+C."""
    try:
        while True:
            print(f"--- worker run at {datetime.now(UTC).isoformat(timespec='seconds')}")
            _cmd_run(args)
            time.sleep(args.interval_hours * 3600)
    except KeyboardInterrupt:
        print("worker stopped")
    return 0


def _cmd_apply(_: argparse.Namespace) -> int:
    with SessionLocal() as session:
        r = process_outbox(session)
    print(
        f"files={r.files} candidates={r.candidates} created={r.created} updated={r.updated} "
        f"pending_review={r.pending} confirmed={r.confirmed} duplicates={r.duplicates} "
        f"rejected={len(r.rejected)} errors={len(r.errors)}"
    )
    for line in r.rejected:
        print(f"  rejected: {line}")
    for line in r.warnings[:20]:
        print(f"  warning: {line}")
    for line in r.errors:
        print(f"  error: {line}")
    return 0


def _cmd_review(args: argparse.Namespace) -> int:
    with SessionLocal() as session:
        proposals = pending_proposals(
            session, source=args.source, kind=args.kind, min_confidence=args.min_confidence
        )
        if not proposals:
            print("nothing to review")
            return 0
        if args.summary:
            counts: dict[tuple[str, str, int], int] = {}
            for p in proposals:
                key = (p.source_id, p.kind, p.tier)
                counts[key] = counts.get(key, 0) + 1
            print(f"{len(proposals)} pending")
            for (source_id, kind, tier), n in sorted(counts.items(), key=lambda kv: -kv[1]):
                print(f"  {n:>4}  T{tier} {kind:<6} {source_id}")
            return 0
        for p in proposals[: args.limit]:
            name = event_name_for(session, p)
            print(f"#{p.id} [{p.kind}] T{p.tier} {name}  ({p.source_id}; conf={p.confidence})")
            print(f"    why queued: {p.reason}")
            if p.kind == "update":
                print(f"    {p.field}: {p.old_value!r} -> {p.new_value!r}")
            else:
                n = p.new_value
                labels = [d["label"] for d in n.get("distances", [])]
                summary = f"{n.get('start_date')} {n.get('province')} {n.get('event_type')}"
                print(f"    new: {summary} {labels}")
            if p.evidence:
                print(f"    evidence: {p.evidence[:160]!r}")
        if len(proposals) > args.limit:
            print(f"... {len(proposals) - args.limit} more (use --limit or filters)")
    return 0


def _cmd_decide(args: argparse.Namespace) -> int:
    action = approve if args.command == "approve" else reject
    with SessionLocal() as session:
        ids = list(args.ids)
        if args.all:
            if not (args.source or args.kind or args.min_confidence is not None):
                print("--all needs at least one filter: --source, --kind or --min-confidence")
                return 2
            ids += [
                p.id
                for p in pending_proposals(
                    session, source=args.source, kind=args.kind, min_confidence=args.min_confidence
                )
            ]
        if not ids:
            print("no ids given")
            return 2
        for proposal_id in ids:
            print(action(session, proposal_id, actor="cli"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.ingest")
    commands = parser.add_subparsers(dest="command", required=True)

    sources = commands.add_parser("sources", help="manage the source registry")
    source_commands = sources.add_subparsers(dest="subcommand", required=True)
    sync = source_commands.add_parser("sync", help="load config/sources.yaml into the database")
    sync.add_argument("--file", default=str(DEFAULT_SOURCES_PATH))
    sync.set_defaults(func=_cmd_sources_sync)
    listing = source_commands.add_parser("list", help="show registered sources")
    listing.set_defaults(func=_cmd_sources_list)

    fetch = commands.add_parser("fetch", help="fetch due sources and queue pages for extraction")
    fetch.add_argument("--source", help="only this source id")
    fetch.add_argument("--limit", type=int, default=10, help="max pages per source (default 10)")
    fetch.add_argument("--delay", type=float, default=2.0, help="seconds between requests per host")
    fetch.add_argument("--force", action="store_true", help="ignore refresh_days")
    fetch.set_defaults(func=_cmd_fetch)

    for name, func, helptext in (
        ("run", _cmd_run, "one pass: sync sources, fetch, apply extractor results"),
        ("worker", _cmd_worker, "repeat `run` every N hours"),
    ):
        runner = commands.add_parser(name, help=helptext)
        runner.add_argument("--limit", type=int, default=10, help="max pages per source")
        runner.add_argument("--delay", type=float, default=2.0)
        runner.add_argument("--force", action="store_true", help="ignore refresh_days")
        if name == "worker":
            runner.add_argument("--interval-hours", type=float, default=24.0)
        runner.set_defaults(func=func)
    commands.add_parser("apply", help="process data/outbox into the catalog").set_defaults(
        func=_cmd_apply
    )
    review = commands.add_parser("review", help="list proposals waiting for a decision")
    review.add_argument("--summary", action="store_true", help="counts by source and kind only")
    review.add_argument("--limit", type=int, default=20)
    review.set_defaults(func=_cmd_review)
    decide_parsers = []
    for name in ("approve", "reject"):
        decide_cmd = commands.add_parser(name, help=f"{name} proposals by id or by filter")
        decide_cmd.add_argument("ids", nargs="*", type=int)
        decide_cmd.add_argument(
            "--all", action="store_true", help="every pending proposal matching the filters"
        )
        decide_cmd.set_defaults(func=_cmd_decide)
        decide_parsers.append(decide_cmd)
    for p in (review, *decide_parsers):
        p.add_argument("--source", help="only this source id")
        p.add_argument("--kind", choices=["create", "update"])
        p.add_argument("--min-confidence", type=float)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))
