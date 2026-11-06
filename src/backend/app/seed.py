"""Load events from a YAML file into the database (idempotent upsert by slug).

Usage: python -m app.seed path/to/events.yaml
The product does not ship seed data: events come from the ingestion pipeline.
This loader exists for test fixtures and local development.
"""

import sys
from datetime import date, datetime, time
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, HttpUrl, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Distance, Event


class DistanceSeed(BaseModel):
    label: str
    distance_km: float = Field(gt=0)
    start_time: time | None = None
    fee_vnd: int | None = Field(default=None, ge=0)
    elevation_gain_m: int | None = Field(default=None, ge=0)
    cutoff_minutes: int | None = Field(default=None, gt=0)
    registration_deadline: date | None = None


class EventSeed(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str
    organizer: str | None = None
    event_type: Literal["road", "trail", "mixed"]
    start_date: date
    end_date: date | None = None
    province: str | None = None
    venue: str | None = None
    map_url: HttpUrl | None = None
    description: str | None = None
    status: Literal[
        "scheduled",
        "registration_open",
        "registration_closed",
        "postponed",
        "cancelled",
        "completed",
    ] = "scheduled"
    registration_url: HttpUrl | None = None
    registration_deadline: date | None = None
    source_name: str | None = None
    source_url: HttpUrl | None = None
    last_verified_at: datetime | None = None
    distances: list[DistanceSeed] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_dates(self) -> "EventSeed":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


def load_seed_file(path: Path) -> list[EventSeed]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    events = [EventSeed.model_validate(item) for item in raw.get("events", [])]
    slugs = [e.slug for e in events]
    if len(slugs) != len(set(slugs)):
        raise ValueError("duplicate slug in seed file")
    return events


_EVENT_FIELDS = (
    "name",
    "organizer",
    "event_type",
    "start_date",
    "end_date",
    "province",
    "venue",
    "description",
    "status",
    "registration_deadline",
    "source_name",
    "last_verified_at",
)
_URL_FIELDS = ("map_url", "registration_url", "source_url")


def seed_events(session: Session, events: list[EventSeed]) -> tuple[int, int]:
    """Upsert events by slug. Returns (created, updated)."""
    created = updated = 0
    for item in events:
        event = session.scalar(select(Event).where(Event.slug == item.slug))
        if event is None:
            event = Event(slug=item.slug)
            session.add(event)
            created += 1
        else:
            updated += 1
        for field in _EVENT_FIELDS:
            setattr(event, field, getattr(item, field))
        for field in _URL_FIELDS:
            value = getattr(item, field)
            setattr(event, field, str(value) if value is not None else None)
        if event.id is not None:
            # Remove old rows first: the unit of work would otherwise INSERT the new
            # distances before DELETE-ing the old ones and violate uq_distances_event_label.
            event.distances.clear()
            session.flush()
        event.distances = [Distance(**d.model_dump()) for d in item.distances]
    session.commit()
    return created, updated


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m app.seed path/to/events.yaml")
        return 2
    path = Path(argv[1])
    events = load_seed_file(path)
    with SessionLocal() as session:
        created, updated = seed_events(session, events)
    print(f"seed: {created} created, {updated} updated ({len(events)} events from {path.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
