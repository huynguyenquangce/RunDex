"""Turn extractor output (data/outbox) into catalog changes: verify, normalize, validate, match,
diff, decide by tier, apply or queue for review."""

import shutil
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ingest.apply import apply_proposal, unique_slug
from app.ingest.changes import Change, decide, diff_event, jsonable
from app.ingest.extract import EventCandidate, Extraction, VerifiedCandidate, verify_candidate
from app.ingest.match import find_match
from app.ingest.normalize import EventData, normalize
from app.ingest.validate import validate
from app.models import ChangeProposal, Event, RawDocument, Source

AUTO_ACTOR = "system:auto"


@dataclass
class ApplyReport:
    files: int = 0
    candidates: int = 0
    created: int = 0
    updated: int = 0
    pending: int = 0
    confirmed: int = 0
    duplicates: int = 0
    rejected: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _confidence_for(verified: VerifiedCandidate, change: Change) -> float:
    return verified.confidence.get(change.field, verified.creation_confidence)


def _pending_exists(
    session: Session, kind: str, event_id: int | None, field_name: str | None, new_value: Any
) -> bool:
    query = select(ChangeProposal).where(
        ChangeProposal.status == "pending",
        ChangeProposal.kind == kind,
        ChangeProposal.event_id == event_id
        if event_id is not None
        else ChangeProposal.event_id.is_(None),
    )
    if field_name is not None:
        query = query.where(ChangeProposal.field == field_name)
    return any(p.new_value == new_value for p in session.scalars(query))


def _evidence_for(candidate: EventCandidate, name: str) -> str | None:
    evidence = candidate.fields.get(name)
    return evidence.evidence if evidence else None


def _handle_candidate(
    session: Session,
    candidate: EventCandidate,
    document: RawDocument,
    source: Source,
    today: date,
    threshold: float,
    now: datetime,
    report: ApplyReport,
) -> None:
    label = candidate.name or "(unnamed)"
    verified = verify_candidate(candidate, document.text)
    if not verified.ok:
        report.rejected.append(f"{label}: {verified.reason}")
        return
    if verified.dropped:
        report.warnings.append(f"{label}: dropped unverified fields {', '.join(verified.dropped)}")
    data: EventData = normalize(verified)
    validation = validate(data, source, today)
    if validation.blocking:
        report.rejected.append(f"{label}: " + "; ".join(validation.blocking))
        return
    data = validation.data
    has_issues = bool(validation.warnings or verified.dropped)
    for warning in validation.warnings:
        report.warnings.append(f"{label}: {warning}")

    match = find_match(session, data)
    if match is None:
        payload = jsonable(data.model_dump())
        payload["slug"] = unique_slug(session, data.slug)
        if _pending_exists(session, "create", None, None, payload):
            report.duplicates += 1
            return
        status, reason = decide(
            "create", None, source.tier, verified.creation_confidence, threshold, has_issues
        )
        proposal = ChangeProposal(
            kind="create",
            source_id=source.id,
            raw_document_id=document.id,
            new_value=payload,
            confidence=round(verified.creation_confidence, 2),
            evidence=_evidence_for(candidate, "name"),
            tier=source.tier,
            status="pending",
            reason=reason,
        )
        session.add(proposal)
        session.flush()
        if status == "auto_applied":
            apply_proposal(session, proposal, AUTO_ACTOR, "auto_applied", now)
            report.created += 1
        else:
            report.pending += 1
        return

    changes = diff_event(match, data)
    if not changes:
        report.confirmed += 1
        if source.tier <= 2:
            match.last_verified_at = now
        return
    for change in changes:
        new_json, old_json = jsonable(change.new), jsonable(change.old)
        if _pending_exists(session, "update", match.id, change.field, new_json):
            report.duplicates += 1
            continue
        confidence = _confidence_for(verified, change)
        status, reason = decide(
            "update", change.field, source.tier, confidence, threshold, has_issues
        )
        proposal = ChangeProposal(
            kind="update",
            event_id=match.id,
            source_id=source.id,
            raw_document_id=document.id,
            field=change.field,
            old_value=old_json,
            new_value=new_json,
            confidence=round(confidence, 2),
            evidence=_evidence_for(candidate, change.field),
            tier=source.tier,
            status="pending",
            reason=reason,
        )
        session.add(proposal)
        session.flush()
        if status == "auto_applied" and apply_proposal(
            session, proposal, AUTO_ACTOR, "auto_applied", now
        ):
            report.updated += 1
        else:
            if status == "auto_applied":
                proposal.status = "superseded"
            else:
                report.pending += 1


def process_outbox(
    session: Session,
    data_dir: Path | None = None,
    today: date | None = None,
    threshold: float | None = None,
    now: datetime | None = None,
) -> ApplyReport:
    data_dir = data_dir or settings.ingest_data_dir
    now = now or datetime.now(UTC)
    today = today or now.date()
    threshold = settings.ingest_auto_threshold if threshold is None else threshold
    report = ApplyReport()
    outbox = data_dir / "outbox"
    for path in sorted(outbox.glob("*.json")) if outbox.exists() else []:
        report.files += 1
        try:
            extraction = Extraction.model_validate_json(path.read_text(encoding="utf-8"))
        except (ValidationError, ValueError) as exc:
            report.errors.append(f"{path.name}: invalid JSON or schema ({type(exc).__name__})")
            continue
        document = session.scalar(
            select(RawDocument)
            .where(RawDocument.content_hash == extraction.content_hash)
            .order_by(RawDocument.id.desc())
        )
        if document is None:
            report.errors.append(f"{path.name}: no fetched page with this content_hash")
            continue
        source = session.get(Source, document.source_id)
        assert source is not None
        for candidate in extraction.candidates:
            report.candidates += 1
            _handle_candidate(session, candidate, document, source, today, threshold, now, report)
        session.commit()
        done = outbox / "done"
        done.mkdir(exist_ok=True)
        shutil.move(str(path), str(done / path.name))
        inbox_file = data_dir / "inbox" / path.name
        if inbox_file.exists():
            inbox_file.unlink()
    return report


def approve(session: Session, proposal_id: int, actor: str, now: datetime | None = None) -> str:
    proposal = session.get(ChangeProposal, proposal_id)
    if proposal is None:
        return f"{proposal_id}: not found"
    if proposal.status != "pending":
        return f"{proposal_id}: already {proposal.status}"
    event = apply_proposal(session, proposal, actor, "approved", now)
    if event is None:
        proposal.status = "superseded"
        session.commit()
        return f"{proposal_id}: superseded (the catalog changed since it was proposed)"
    session.commit()
    return f"{proposal_id}: approved -> event {event.slug}"


def reject(session: Session, proposal_id: int, actor: str, now: datetime | None = None) -> str:
    proposal = session.get(ChangeProposal, proposal_id)
    if proposal is None:
        return f"{proposal_id}: not found"
    if proposal.status != "pending":
        return f"{proposal_id}: already {proposal.status}"
    proposal.status = "rejected"
    proposal.decided_by = actor
    proposal.decided_at = now or datetime.now(UTC)
    session.commit()
    return f"{proposal_id}: rejected"


def pending_proposals(session: Session) -> list[ChangeProposal]:
    return list(
        session.scalars(
            select(ChangeProposal)
            .where(ChangeProposal.status == "pending")
            .order_by(ChangeProposal.id)
        )
    )


def event_name_for(session: Session, proposal: ChangeProposal) -> str:
    if proposal.kind == "create":
        return str(proposal.new_value.get("name"))
    event = session.get(Event, proposal.event_id) if proposal.event_id else None
    return event.name if event else "?"
