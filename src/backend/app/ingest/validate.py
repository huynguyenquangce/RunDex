"""Deterministic checks on a normalized event. No AI involved."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from urllib.parse import urlsplit

from app.ingest.normalize import EventData
from app.models import Source

PAST_LIMIT = timedelta(days=400)
FUTURE_LIMIT = timedelta(days=1100)
# Ticketing platforms an organizer may legitimately link to.
TICKETING_HOSTS = {"irace.vn", "ticketbox.vn", "5bib.com"}


@dataclass
class ValidationResult:
    data: EventData
    blocking: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _host(url: str) -> str:
    return (urlsplit(url).hostname or "").removeprefix("www.")


def same_site(a: str, b: str) -> bool:
    return a == b or a.endswith("." + b) or b.endswith("." + a)


def validate(data: EventData, source: Source, today: date) -> ValidationResult:
    result = ValidationResult(data=data.model_copy(deep=True))
    d = result.data
    if not d.name.strip():
        result.blocking.append("empty name")
    if d.start_date < today - PAST_LIMIT or d.start_date > today + FUTURE_LIMIT:
        result.blocking.append(f"start date {d.start_date} is out of the plausible range")
    if d.end_date is not None and d.end_date < d.start_date:
        result.blocking.append("end date is before start date")
    if d.event_type is None:
        result.warnings.append("event type missing or not recognised")
    if d.province is None:
        result.warnings.append("province missing")
    if d.registration_deadline and d.registration_deadline > d.start_date:
        result.warnings.append("registration deadline is after the event; dropped")
        d.registration_deadline = None

    if d.registration_url:
        parts = urlsplit(d.registration_url)
        host = _host(d.registration_url)
        if parts.scheme not in ("http", "https") or not host:
            result.warnings.append("registration URL is not a valid http(s) link; dropped")
            d.registration_url = None
        elif source.tier <= 2:
            source_host = _host(source.url)
            if not (same_site(host, source_host) or host in TICKETING_HOSTS):
                result.warnings.append(
                    f"registration URL host {host} differs from the source; dropped"
                )
                d.registration_url = None
    return result
