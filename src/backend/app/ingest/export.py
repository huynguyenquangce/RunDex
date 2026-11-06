"""Export the catalog to YAML in the format `python -m app.seed` loads."""

from datetime import UTC, datetime
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Event

_SCALARS = (
    "slug",
    "name",
    "organizer",
    "event_type",
    "start_date",
    "end_date",
    "province",
    "venue",
    "map_url",
    "description",
    "status",
    "registration_url",
    "registration_deadline",
    "source_name",
    "source_url",
    "last_verified_at",
)


def _plain(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def export_catalog(session: Session) -> list[dict[str, Any]]:
    events = session.scalars(
        select(Event).options(selectinload(Event.distances)).order_by(Event.start_date, Event.slug)
    )
    out: list[dict[str, Any]] = []
    for event in events:
        item = {name: _plain(getattr(event, name)) for name in _SCALARS}
        item = {k: v for k, v in item.items() if v is not None}
        item["distances"] = [
            {
                k: _plain(v)
                for k, v in {
                    "label": d.label,
                    "distance_km": float(d.distance_km),
                    "start_time": d.start_time,
                    "fee_vnd": d.fee_vnd,
                    "elevation_gain_m": d.elevation_gain_m,
                    "cutoff_minutes": d.cutoff_minutes,
                    "registration_deadline": d.registration_deadline,
                }.items()
                if v is not None
            }
            for d in event.distances
        ]
        out.append(item)
    return out


def catalog_yaml(session: Session, now: datetime | None = None) -> str:
    stamp = (now or datetime.now(UTC)).strftime("%Y-%m-%d")
    header = (
        f"# RunDex catalog snapshot, exported {stamp}.\n"
        "# Events collected by the ingestion pipeline and reviewed by a person.\n"
        "# Facts only (name, date, place, distances, status), with the source of each event.\n"
        "# Load into an empty database: python -m app.seed catalog/events.snapshot.yaml\n"
    )
    body = yaml.safe_dump(
        {"events": export_catalog(session)}, allow_unicode=True, sort_keys=False, width=100
    )
    return header + body
