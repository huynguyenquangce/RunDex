import base64
import json
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy import ColumnElement, Select, and_, exists, func, or_, select, tuple_
from sqlalchemy.orm import Session, selectinload

from app.core.regions import REGIONS
from app.models import Distance, Event
from app.schemas import DistanceBrief, DistanceOut, EventDetail, EventSummary

CLOSING_SOON_DAYS = 7
MAX_QUERY_LENGTH = 100
# Distance filter buckets: label -> (min_km, max_km), both inclusive.
DISTANCE_BUCKETS: dict[str, tuple[float, float]] = {
    "5": (4.5, 6.0),
    "10": (9.0, 11.0),
    "21": (20.0, 22.0),
    "42": (41.0, 43.0),
    "ultra": (50.0, 10_000.0),
}


@dataclass
class EventFilters:
    q: str | None = None
    event_type: str | None = None
    distances: list[str] = field(default_factory=list)
    region: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    open_only: bool = False
    include_past: bool = False


# ---- cursor (keyset pagination on (start_date, id)) ----------------------------------------


def encode_cursor(start_date: date, event_id: int) -> str:
    raw = json.dumps({"d": start_date.isoformat(), "i": event_id}).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[date, int]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode()))
        return date.fromisoformat(data["d"]), int(data["i"])
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("invalid cursor") from exc


# ---- derived fields -----------------------------------------------------------------------


def days_left(event: Event, today: date) -> int | None:
    if event.registration_deadline is None:
        return None
    left = (event.registration_deadline - today).days
    return left if left >= 0 else None


def effective_status(event: Event, today: date) -> str:
    if event.status == "cancelled":
        return "cancelled"
    last_day = event.end_date or event.start_date
    if last_day < today:
        return "completed"
    if (
        event.status == "registration_open"
        and event.registration_deadline is not None
        and event.registration_deadline < today
    ):
        return "registration_closed"
    return event.status


def is_closing_soon(event: Event, today: date) -> bool:
    left = days_left(event, today)
    return (
        effective_status(event, today) == "registration_open"
        and left is not None
        and left <= CLOSING_SOON_DAYS
    )


def _base_fields(event: Event, today: date) -> dict[str, object]:
    return {
        "slug": event.slug,
        "name": event.name,
        "organizer": event.organizer,
        "event_type": event.event_type,
        "start_date": event.start_date,
        "end_date": event.end_date,
        "province": event.province,
        "venue": event.venue,
        "status": effective_status(event, today),
        "closing_soon": is_closing_soon(event, today),
        "days_left": days_left(event, today),
        "verified": event.last_verified_at is not None,
        "last_verified_at": event.last_verified_at,
    }


def to_summary(event: Event, today: date) -> EventSummary:
    return EventSummary(
        **_base_fields(event, today),
        distances=[
            DistanceBrief(label=d.label, distance_km=float(d.distance_km)) for d in event.distances
        ],
    )


def to_detail(event: Event, today: date) -> EventDetail:
    return EventDetail(
        **_base_fields(event, today),
        description=event.description,
        map_url=event.map_url,
        registration_url=event.registration_url,
        registration_deadline=event.registration_deadline,
        source_name=event.source_name,
        source_url=event.source_url,
        distances=[
            DistanceOut(
                label=d.label,
                distance_km=float(d.distance_km),
                start_time=d.start_time,
                fee_vnd=d.fee_vnd,
                elevation_gain_m=d.elevation_gain_m,
                cutoff_minutes=d.cutoff_minutes,
                registration_deadline=d.registration_deadline,
            )
            for d in event.distances
        ],
    )


# ---- queries ------------------------------------------------------------------------------


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def build_conditions(f: EventFilters, today: date) -> list[ColumnElement[bool]]:
    conds: list[ColumnElement[bool]] = []
    last_day = func.coalesce(Event.end_date, Event.start_date)
    if f.date_from is not None:
        conds.append(last_day >= f.date_from)
    elif not f.include_past:
        conds.append(last_day >= today)
    if f.date_to is not None:
        conds.append(Event.start_date <= f.date_to)
    if f.event_type is not None:
        conds.append(Event.event_type == f.event_type)
    if f.region is not None:
        conds.append(Event.province.in_(REGIONS[f.region]))
    if f.q:
        for token in f.q[:MAX_QUERY_LENGTH].split():
            normalized = func.lower(func.f_unaccent(_escape_like(token)))
            conds.append(Event.search_text.like(func.concat("%", normalized, "%"), escape="\\"))
    if f.distances:
        ranges = [
            and_(Distance.distance_km >= lo, Distance.distance_km <= hi)
            for lo, hi in (DISTANCE_BUCKETS[b] for b in f.distances)
        ]
        conds.append(exists().where(Distance.event_id == Event.id, or_(*ranges)))
    if f.open_only:
        conds.append(Event.status == "registration_open")
        conds.append(
            or_(Event.registration_deadline.is_(None), Event.registration_deadline >= today)
        )
    return conds


def page_statement(
    f: EventFilters, today: date, limit: int, cursor: tuple[date, int] | None
) -> Select[tuple[Event]]:
    stmt = select(Event).where(*build_conditions(f, today))
    if cursor is not None:
        stmt = stmt.where(tuple_(Event.start_date, Event.id) > tuple_(*cursor))
    return (
        stmt.order_by(Event.start_date, Event.id)
        .limit(limit + 1)
        .options(selectinload(Event.distances))
    )


def list_events(
    session: Session, f: EventFilters, today: date, limit: int, cursor: tuple[date, int] | None
) -> tuple[list[Event], str | None, int, datetime | None]:
    rows = list(session.scalars(page_statement(f, today, limit, cursor)))
    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        last = rows[-1]
        next_cursor = encode_cursor(last.start_date, last.id)
    total = session.scalar(
        select(func.count()).select_from(Event).where(*build_conditions(f, today))
    )
    last_updated = session.scalar(select(func.max(Event.updated_at)))
    return rows, next_cursor, total or 0, last_updated


def get_event_by_slug(session: Session, slug: str) -> Event | None:
    return session.scalar(
        select(Event).where(Event.slug == slug).options(selectinload(Event.distances))
    )
