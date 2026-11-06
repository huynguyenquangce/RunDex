"""Command line entry point: python -m app.ingest <command>."""

import argparse
from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))
