"""Diff a candidate against a stored event, and decide by trust tier what may be applied alone."""

from dataclasses import dataclass
from datetime import date, time
from typing import Any

from app.ingest.normalize import DistanceData, EventData
from app.models import Event

SCALAR_FIELDS = (
    "organizer",
    "event_type",
    "start_date",
    "end_date",
    "province",
    "venue",
    "status",
    "registration_url",
    "registration_deadline",
)
# Changes that could mislead a runner are never applied without a person (tier 2 and 3).
HIGH_IMPACT = {
    "start_date",
    "end_date",
    "status",
    "province",
    "venue",
    "registration_url",
    "registration_deadline",
    "event_type",
}


@dataclass
class Change:
    field: str
    old: Any
    new: Any


def jsonable(value: Any) -> Any:
    if isinstance(value, date | time):
        return value.isoformat()
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    return value


def distance_dict(d: Any) -> dict[str, Any]:
    return {
        "label": d.label,
        "distance_km": round(float(d.distance_km), 2),
        "start_time": d.start_time.isoformat() if d.start_time else None,
        "fee_vnd": d.fee_vnd,
        "elevation_gain_m": d.elevation_gain_m,
        "cutoff_minutes": d.cutoff_minutes,
        "registration_deadline": d.registration_deadline.isoformat()
        if d.registration_deadline
        else None,
    }


def merge_distances(existing: list[Any], new: list[DistanceData]) -> list[dict[str, Any]]:
    """New list wins for labels it contains, but never blanks a value we already know."""
    old_by_label = {d.label: distance_dict(d) for d in existing}
    merged: dict[str, dict[str, Any]] = dict(old_by_label)
    for d in new:
        incoming = distance_dict(d)
        base = old_by_label.get(d.label, {})
        merged[d.label] = {
            k: incoming[k] if incoming[k] is not None else base.get(k) for k in incoming
        }
    return sorted(merged.values(), key=lambda x: -x["distance_km"])


def diff_event(event: Event, data: EventData) -> list[Change]:
    changes: list[Change] = []
    for name in SCALAR_FIELDS:
        new = getattr(data, name)
        old = getattr(event, name)
        if new is None or new == old:
            continue
        if name == "status" and new == "scheduled":
            continue  # "scheduled" from a page means "nothing said", not a regression
        changes.append(Change(name, old, new))
    if data.distances:
        old_list = [distance_dict(d) for d in sorted(event.distances, key=lambda d: -d.distance_km)]
        merged = merge_distances(event.distances, data.distances)
        if merged != old_list:
            changes.append(Change("distances", old_list, merged))
    return changes


def decide(
    kind: str, field: str | None, tier: int, confidence: float, threshold: float, has_issues: bool
) -> tuple[str, str]:
    """Return ("auto_applied" | "pending", reason)."""
    if tier == 3:
        return "pending", "tier 3 sources are always reviewed"
    if confidence < threshold:
        return "pending", f"confidence {confidence:.2f} is below {threshold:.2f}"
    if kind == "create":
        if has_issues:
            return "pending", "validation warnings on a new event"
        return "auto_applied", "official source, new event, confidence above threshold"
    if field in HIGH_IMPACT:
        return "pending", f"{field} is a high-impact field"
    return "auto_applied", "official source, low-impact field, confidence above threshold"
