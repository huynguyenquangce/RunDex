"""Write approved or auto-applied proposals to the catalog, with an audit trail."""

from datetime import UTC, date, datetime, time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingest.changes import distance_dict, merge_distances
from app.ingest.normalize import DistanceData
from app.models import AuditLog, ChangeProposal, Distance, Event, RawDocument, Source

DATE_FIELDS = {"start_date", "end_date", "registration_deadline"}


def _distance(d: dict[str, Any]) -> Distance:
    return Distance(
        label=d["label"],
        distance_km=d["distance_km"],
        start_time=time.fromisoformat(d["start_time"]) if d.get("start_time") else None,
        fee_vnd=d.get("fee_vnd"),
        elevation_gain_m=d.get("elevation_gain_m"),
        cutoff_minutes=d.get("cutoff_minutes"),
        registration_deadline=date.fromisoformat(d["registration_deadline"])
        if d.get("registration_deadline")
        else None,
    )


def unique_slug(session: Session, slug: str) -> str:
    candidate, n = slug, 1
    while session.scalar(select(Event.id).where(Event.slug == candidate)) is not None:
        n += 1
        candidate = f"{slug}-{n}"
    return candidate


def _verified_stamp(source: Source, now: datetime, approved: bool) -> datetime | None:
    """Official sources verify at fetch time; other sources only once a person approves."""
    return now if (source.tier <= 2 or approved) else None


def apply_proposal(
    session: Session,
    proposal: ChangeProposal,
    actor: str,
    status: str,
    now: datetime | None = None,
) -> Event | None:
    """Apply one proposal. Returns the event, or None if the proposal is stale (superseded)."""
    now = now or datetime.now(UTC)
    source = session.get(Source, proposal.source_id)
    document = (
        session.get(RawDocument, proposal.raw_document_id) if proposal.raw_document_id else None
    )
    assert source is not None
    approved = status == "approved"

    if proposal.kind == "create":
        data = dict(proposal.new_value)
        event = Event(
            slug=unique_slug(session, data["slug"]),
            name=data["name"],
            organizer=data.get("organizer"),
            event_type=data.get("event_type") or "mixed",
            start_date=date.fromisoformat(data["start_date"]),
            end_date=date.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            province=data.get("province"),
            venue=data.get("venue"),
            status=data.get("status") or "scheduled",
            registration_url=data.get("registration_url"),
            registration_deadline=date.fromisoformat(data["registration_deadline"])
            if data.get("registration_deadline")
            else None,
            source_name=source.name,
            source_url=document.url if document else source.url,
            last_verified_at=_verified_stamp(source, now, approved),
        )
        event.distances = [_distance(d) for d in data.get("distances", [])]
        session.add(event)
        session.flush()
        action = "event_created"
    else:
        event = session.get(Event, proposal.event_id) if proposal.event_id else None
        if event is None:
            return None
        field = proposal.field or ""
        if field == "distances":
            current = [d for d in event.distances]
            expected = proposal.old_value
            if [
                distance_dict(d) for d in sorted(current, key=lambda d: -d.distance_km)
            ] != expected:
                return None
            new_distances = [DistanceData.model_validate(d) for d in proposal.new_value]
            merged = merge_distances(current, new_distances)
            event.distances.clear()
            session.flush()
            event.distances = [_distance(d) for d in merged]
        else:
            current_value = getattr(event, field)
            current_json = (
                current_value.isoformat() if isinstance(current_value, date) else current_value
            )
            if current_json != proposal.old_value:
                return None  # the catalog changed since this proposal was made
            new_value = proposal.new_value
            setattr(
                event, field, date.fromisoformat(new_value) if field in DATE_FIELDS else new_value
            )
        stamp = _verified_stamp(source, now, approved)
        if stamp is not None:
            event.last_verified_at = stamp
        action = "event_updated"

    proposal.event_id = event.id
    proposal.status = status
    proposal.decided_by = actor
    proposal.decided_at = now
    session.add(
        AuditLog(
            actor=actor,
            action=action,
            event_id=event.id,
            proposal_id=proposal.id,
            details={"field": proposal.field, "old": proposal.old_value, "new": proposal.new_value},
        )
    )
    return event
