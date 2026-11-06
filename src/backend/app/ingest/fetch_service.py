"""Fetch the pages of registered sources and queue new or changed ones for extraction."""

import hashlib
import json
import textwrap
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ingest.discover import discover_urls
from app.ingest.fetcher import Fetcher
from app.models import RawDocument, Source


@dataclass
class FetchReport:
    source_id: str
    discovered: int = 0
    new_or_changed: int = 0
    unchanged: int = 0
    skipped: list[str] = field(default_factory=list)


READ_WIDTH = 400


def wrap_for_reading(text: str) -> str:
    """Break very long lines at spaces so tools that read files in slices do not truncate them.

    Only whitespace changes, and evidence matching ignores whitespace differences.
    """
    lines = []
    for line in text.split("\n"):
        if len(line) <= READ_WIDTH:
            lines.append(line)
        else:
            lines.append(
                textwrap.fill(line, READ_WIDTH, break_long_words=False, break_on_hyphens=False)
            )
    return "\n".join(lines)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _latest_document(session: Session, url: str) -> RawDocument | None:
    return session.scalar(
        select(RawDocument).where(RawDocument.url == url).order_by(RawDocument.fetched_at.desc())
    )


def _write_inbox(data_dir: Path, document: RawDocument) -> Path:
    outbox_file = data_dir / "outbox" / f"{document.content_hash}.json"
    inbox_file = data_dir / "inbox" / f"{document.content_hash}.json"
    if outbox_file.exists() or inbox_file.exists():
        return inbox_file
    inbox_file.parent.mkdir(parents=True, exist_ok=True)
    # The page text goes to its own multi-line .txt so tools can read it in slices.
    text_file = inbox_file.with_suffix(".txt")
    text_file.write_text(wrap_for_reading(document.text), encoding="utf-8")
    payload = {
        "content_hash": document.content_hash,
        "url": document.url,
        "source_id": document.source_id,
        "fetched_at": document.fetched_at.isoformat(),
        "text_file": text_file.name,
        "text_chars": len(document.text),
    }
    inbox_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return inbox_file


def is_due(source: Source, now: datetime) -> bool:
    if source.last_fetched_at is None:
        return True
    return now - source.last_fetched_at >= timedelta(days=source.refresh_days)


def fetch_source(
    session: Session,
    source: Source,
    fetcher: Fetcher,
    limit: int,
    data_dir: Path | None = None,
    now: datetime | None = None,
) -> FetchReport:
    data_dir = data_dir or settings.ingest_data_dir
    now = now or datetime.now(UTC)
    report = FetchReport(source.id)
    urls = discover_urls(source, fetcher, limit)
    report.discovered = len(urls)
    for url in urls:
        previous = _latest_document(session, url)
        result = fetcher.fetch(
            url,
            etag=previous.etag if previous else None,
            last_modified=previous.last_modified if previous else None,
        )
        if result.not_modified:
            report.unchanged += 1
            continue
        if result.text is None:
            report.skipped.append(f"{url}: {result.skipped}")
            continue
        digest = content_hash(result.text)
        if previous is not None and previous.content_hash == digest:
            report.unchanged += 1
            continue
        document = RawDocument(
            source_id=source.id,
            url=url,
            fetched_at=now,
            http_status=result.status or 200,
            content_hash=digest,
            text=result.text,
            etag=result.etag,
            last_modified=result.last_modified,
        )
        session.add(document)
        session.flush()
        _write_inbox(data_dir, document)
        report.new_or_changed += 1
    source.last_fetched_at = now
    session.commit()
    return report
