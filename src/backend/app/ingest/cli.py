"""Command line entry point: python -m app.ingest <command>."""

import argparse
from datetime import UTC, datetime
from pathlib import Path

import httpx
from sqlalchemy import select

from app.db import SessionLocal
from app.ingest.fetch_service import fetch_source, is_due
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


def _cmd_fetch(args: argparse.Namespace) -> int:
    now = datetime.now(UTC)
    with (
        SessionLocal() as session,
        httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=20.0, follow_redirects=True
        ) as client,
    ):
        fetcher = Fetcher(client, delay_seconds=args.delay)
        query = select(Source).where(Source.enabled).order_by(Source.tier, Source.id)
        if args.source:
            query = query.where(Source.id == args.source)
        sources = [s for s in session.scalars(query) if args.force or is_due(s, now)]
        if not sources:
            print("nothing due (use --force to fetch anyway)")
        for source in sources:
            report = fetch_source(session, source, fetcher, limit=args.limit, now=now)
            print(
                f"{source.id:<24} discovered={report.discovered} "
                f"new_or_changed={report.new_or_changed} unchanged={report.unchanged} "
                f"skipped={len(report.skipped)}"
            )
            for line in report.skipped[:3]:
                print(f"    skipped: {line}")
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


def _cmd_review(_: argparse.Namespace) -> int:
    with SessionLocal() as session:
        proposals = pending_proposals(session)
        if not proposals:
            print("nothing to review")
        for p in proposals:
            name = event_name_for(session, p)
            print(f"#{p.id} [{p.kind}] T{p.tier} {name}  ({p.source_id}; conf={p.confidence})")
            print(f"    why queued: {p.reason}")
            if p.kind == "update":
                print(f"    {p.field}: {p.old_value!r} -> {p.new_value!r}")
            else:
                n = p.new_value
                print(
                    f"    new: {n.get('start_date')} {n.get('province')} {n.get('event_type')}"
                    f" distances={[d['label'] for d in n.get('distances', [])]}"
                )
            if p.evidence:
                print(f"    evidence: {p.evidence[:160]!r}")
    return 0


def _cmd_decide(args: argparse.Namespace) -> int:
    action = approve if args.command == "approve" else reject
    with SessionLocal() as session:
        for proposal_id in args.ids:
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

    commands.add_parser("apply", help="process data/outbox into the catalog").set_defaults(
        func=_cmd_apply
    )
    commands.add_parser("review", help="list proposals waiting for a decision").set_defaults(
        func=_cmd_review
    )
    for name in ("approve", "reject"):
        decide_cmd = commands.add_parser(name, help=f"{name} proposals by id")
        decide_cmd.add_argument("ids", nargs="+", type=int)
        decide_cmd.set_defaults(func=_cmd_decide)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))
