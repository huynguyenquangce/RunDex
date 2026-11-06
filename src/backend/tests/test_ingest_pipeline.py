import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ingest.pipeline import approve, pending_proposals, process_outbox, reject
from app.models import AuditLog, ChangeProposal, Distance, Event, RawDocument, Source

TODAY = date(2026, 11, 6)
NOW = datetime(2026, 11, 6, 9, 0, tzinfo=UTC)
PAGE = (
    "Vietnam Trail Marathon 2027\nNgày thi đấu: 16/01/2027\nĐịa điểm: Mộc Châu, Sơn La\n"
    "Cự ly: 70K, 50K\nĐăng ký tại https://vietnamtrailseries.com/book\nBan tổ chức: Topas Travel"
)


def make_source(db: Session, tier: int = 2, source_id: str = "vts") -> Source:
    source = Source(
        id=source_id,
        name="VTS",
        kind="sitemap",
        url="https://vietnamtrailseries.com/s.xml",
        tier=tier,
    )
    db.add(source)
    db.commit()
    return source


def make_document(db: Session, source: Source, digest: str, text: str = PAGE) -> RawDocument:
    doc = RawDocument(
        source_id=source.id, url=f"https://vietnamtrailseries.com/{digest}", http_status=200,
        content_hash=digest, text=text,
    )  # fmt: skip
    db.add(doc)
    db.commit()
    return doc


def candidate(**overrides: object) -> dict:
    base: dict = {
        "name": "Vietnam Trail Marathon 2027",
        "event_type": "trail",
        "start_date": "2027-01-16",
        "province": "Sơn La",
        "venue": "Mộc Châu",
        "organizer": "Topas Travel",
        "distances": [{"label": "70K", "distance_km": 70}, {"label": "50K", "distance_km": 50}],
        "fields": {
            "name": {"confidence": 0.95, "evidence": "Vietnam Trail Marathon 2027"},
            "event_type": {"confidence": 0.9, "evidence": "Trail"},
            "start_date": {"confidence": 0.95, "evidence": "Ngày thi đấu: 16/01/2027"},
            "province": {"confidence": 0.9, "evidence": "Mộc Châu, Sơn La"},
            "venue": {"confidence": 0.9, "evidence": "Mộc Châu"},
            "organizer": {"confidence": 0.9, "evidence": "Ban tổ chức: Topas Travel"},
            "distances": {"confidence": 0.9, "evidence": "Cự ly: 70K, 50K"},
        },
    }
    base.update(overrides)
    return base


def write_outbox(data_dir: Path, digest: str, *candidates: dict) -> Path:
    outbox = data_dir / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    path = outbox / f"{digest}.json"
    payload = {"content_hash": digest, "source_url": "x", "candidates": list(candidates)}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def run(db: Session, tmp_path: Path, threshold: float = 0.85):
    return process_outbox(db, data_dir=tmp_path, today=TODAY, threshold=threshold, now=NOW)


def count(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


def test_official_high_confidence_candidate_creates_an_event(db: Session, tmp_path: Path) -> None:
    source = make_source(db)
    make_document(db, source, "h1")
    path = write_outbox(tmp_path, "h1", candidate())

    report = run(db, tmp_path)
    assert (report.created, report.pending, report.rejected) == (1, 0, [])

    event = db.scalars(select(Event)).one()
    assert event.slug == "vietnam-trail-marathon-2027"
    assert event.province == "Sơn La" and event.event_type == "trail"
    assert [d.label for d in event.distances] == ["70K", "50K"]
    assert event.source_name == "VTS" and event.last_verified_at is not None
    proposal = db.scalars(select(ChangeProposal)).one()
    assert proposal.status == "auto_applied" and proposal.event_id == event.id
    audit = db.scalars(select(AuditLog)).one()
    assert (audit.actor, audit.action, audit.event_id) == ("system:auto", "event_created", event.id)
    assert not path.exists() and (tmp_path / "outbox" / "done" / "h1.json").exists()
    assert run(db, tmp_path).files == 0


def test_candidate_with_invented_evidence_is_rejected(db: Session, tmp_path: Path) -> None:
    source = make_source(db)
    make_document(db, source, "h1")
    bad = candidate()
    bad["fields"]["start_date"]["evidence"] = "Ngày thi đấu: 20/03/2027"
    write_outbox(tmp_path, "h1", bad)

    report = run(db, tmp_path)
    assert report.created == 0 and len(report.rejected) == 1
    assert count(db, Event) == 0 and count(db, ChangeProposal) == 0


def test_unverified_optional_field_is_dropped_and_event_waits_for_review(
    db: Session, tmp_path: Path
) -> None:
    source = make_source(db)
    make_document(db, source, "h1")
    cand = candidate()
    cand["fields"]["venue"]["evidence"] = "Công viên Thống Nhất"
    write_outbox(tmp_path, "h1", cand)

    report = run(db, tmp_path)
    assert (report.created, report.pending) == (0, 1)
    assert any("venue" in w for w in report.warnings)
    assert pending_proposals(db)[0].new_value["venue"] is None


def test_tier3_candidate_waits_for_review_then_approval_creates_it(
    db: Session, tmp_path: Path
) -> None:
    source = make_source(db, tier=3, source_id="blog")
    make_document(db, source, "h1")
    write_outbox(tmp_path, "h1", candidate())

    report = run(db, tmp_path)
    assert (report.created, report.pending) == (0, 1)
    assert count(db, Event) == 0
    (proposal,) = pending_proposals(db)

    assert "approved" in approve(db, proposal.id, actor="cli", now=NOW)
    event = db.scalars(select(Event)).one()
    assert event.last_verified_at == NOW  # verified by a person at approval time
    db.refresh(proposal)
    assert proposal.status == "approved" and proposal.decided_by == "cli"
    assert db.scalars(select(AuditLog)).one().actor == "cli"
    assert "already approved" in approve(db, proposal.id, actor="cli")


def test_tier3_event_is_not_stamped_verified_until_approved(db: Session, tmp_path: Path) -> None:
    source = make_source(db, tier=3, source_id="blog")
    make_document(db, source, "h1")
    write_outbox(tmp_path, "h1", candidate())
    run(db, tmp_path)
    approve(db, pending_proposals(db)[0].id, actor="cli", now=NOW)
    assert db.scalars(select(Event)).one().last_verified_at is not None


def test_rejecting_a_proposal_changes_nothing(db: Session, tmp_path: Path) -> None:
    source = make_source(db, tier=3, source_id="blog")
    make_document(db, source, "h1")
    write_outbox(tmp_path, "h1", candidate())
    run(db, tmp_path)
    (proposal,) = pending_proposals(db)
    assert "rejected" in reject(db, proposal.id, actor="cli")
    assert count(db, Event) == 0 and not pending_proposals(db)


def test_same_pending_candidate_from_two_pages_is_queued_once(db: Session, tmp_path: Path) -> None:
    source = make_source(db, tier=3, source_id="blog")
    make_document(db, source, "h1")
    make_document(db, source, "h2")
    write_outbox(tmp_path, "h1", candidate())
    run(db, tmp_path)
    write_outbox(tmp_path, "h2", candidate())
    report = run(db, tmp_path)
    assert report.duplicates == 1 and count(db, ChangeProposal) == 1


def test_low_confidence_official_candidate_waits_for_review(db: Session, tmp_path: Path) -> None:
    source = make_source(db)
    make_document(db, source, "h1")
    cand = candidate()
    cand["fields"]["start_date"]["confidence"] = 0.6
    write_outbox(tmp_path, "h1", cand)
    report = run(db, tmp_path)
    assert (report.created, report.pending) == (0, 1)


def _existing_event(db: Session, tmp_path: Path) -> Event:
    source = make_source(db)
    make_document(db, source, "h1")
    write_outbox(tmp_path, "h1", candidate())
    run(db, tmp_path)
    return db.scalars(select(Event)).one()


def test_changed_date_from_an_official_page_needs_a_person(db: Session, tmp_path: Path) -> None:
    event = _existing_event(db, tmp_path)
    page = PAGE.replace("16/01/2027", "23/01/2027")
    make_document(db, db.get(Source, "vts"), "h2", page)
    moved = candidate(start_date="2027-01-23")
    moved["fields"]["start_date"]["evidence"] = "Ngày thi đấu: 23/01/2027"
    write_outbox(tmp_path, "h2", moved)

    report = run(db, tmp_path)
    assert (report.updated, report.pending, report.created) == (0, 1, 0)
    db.refresh(event)
    assert event.start_date == date(2027, 1, 16)
    (proposal,) = pending_proposals(db)
    assert (proposal.field, proposal.old_value, proposal.new_value) == (
        "start_date", "2027-01-16", "2027-01-23",
    )  # fmt: skip

    approve(db, proposal.id, actor="cli", now=NOW)
    db.refresh(event)
    assert event.start_date == date(2027, 1, 23)


def test_low_impact_change_from_an_official_page_is_applied_automatically(
    db: Session, tmp_path: Path
) -> None:
    event = _existing_event(db, tmp_path)
    make_document(db, db.get(Source, "vts"), "h2", PAGE + "\nBan tổ chức: Topas Explorer Group")
    changed = candidate(organizer="Topas Explorer Group")
    changed["fields"]["organizer"]["evidence"] = "Ban tổ chức: Topas Explorer Group"
    write_outbox(tmp_path, "h2", changed)

    report = run(db, tmp_path)
    assert (report.updated, report.pending) == (1, 0)
    db.refresh(event)
    assert event.organizer == "Topas Explorer Group"
    assert db.scalars(select(AuditLog).where(AuditLog.action == "event_updated")).one()


def test_similar_name_and_nearby_date_matches_the_existing_event(
    db: Session, tmp_path: Path
) -> None:
    _existing_event(db, tmp_path)
    page = "VTM Vietnam Trail Marathon\nNgày: 17/01/2027"
    make_document(db, db.get(Source, "vts"), "h2", page)
    other = {
        "name": "Vietnam Trail Marathon",
        "start_date": "2027-01-17",
        "fields": {
            "name": {"confidence": 0.9, "evidence": "Vietnam Trail Marathon"},
            "start_date": {"confidence": 0.9, "evidence": "Ngày: 17/01/2027"},
        },
    }
    write_outbox(tmp_path, "h2", other)
    report = run(db, tmp_path)
    assert report.created == 0 and count(db, Event) == 1
    assert report.pending == 1  # the one-day date difference is queued, not published


def test_unchanged_official_page_confirms_the_event(db: Session, tmp_path: Path) -> None:
    event = _existing_event(db, tmp_path)
    event.last_verified_at = None
    db.commit()
    make_document(db, db.get(Source, "vts"), "h2", PAGE + " ")
    write_outbox(tmp_path, "h2", candidate())
    report = run(db, tmp_path)
    assert report.confirmed == 1
    db.refresh(event)
    assert event.last_verified_at == NOW


def test_stale_proposal_is_superseded(db: Session, tmp_path: Path) -> None:
    event = _existing_event(db, tmp_path)
    make_document(db, db.get(Source, "vts"), "h2", PAGE.replace("16/01/2027", "23/01/2027"))
    moved = candidate(start_date="2027-01-23")
    moved["fields"]["start_date"]["evidence"] = "Ngày thi đấu: 23/01/2027"
    write_outbox(tmp_path, "h2", moved)
    run(db, tmp_path)
    (proposal,) = pending_proposals(db)
    event.start_date = date(2027, 1, 30)  # someone changed the catalog in the meantime
    db.commit()
    assert "superseded" in approve(db, proposal.id, actor="cli")
    db.refresh(event)
    assert event.start_date == date(2027, 1, 30)


def test_invalid_outbox_file_and_unknown_hash_are_reported(db: Session, tmp_path: Path) -> None:
    make_source(db)
    (tmp_path / "outbox").mkdir()
    (tmp_path / "outbox" / "bad.json").write_text("{not json", encoding="utf-8")
    write_outbox(tmp_path, "ghost", candidate())
    report = run(db, tmp_path)
    assert len(report.errors) == 2 and report.created == 0


@pytest.mark.parametrize("distance_count", [0, 2])
def test_distances_are_stored_with_the_event(
    db: Session, tmp_path: Path, distance_count: int
) -> None:
    source = make_source(db)
    make_document(db, source, "h1")
    cand = candidate()
    cand["distances"] = cand["distances"][:distance_count]
    if distance_count == 0:
        cand["fields"].pop("distances")
    write_outbox(tmp_path, "h1", cand)
    run(db, tmp_path)
    assert count(db, Distance) == distance_count


def test_same_event_from_two_sources_is_queued_once_with_corroboration(
    db: Session, tmp_path: Path
) -> None:
    first = make_source(db, tier=3, source_id="blog-a")
    second = make_source(db, tier=3, source_id="blog-b")
    make_document(db, first, "h1")
    make_document(db, second, "h2")
    write_outbox(tmp_path, "h1", candidate())
    run(db, tmp_path)
    other = candidate(name="Vietnam Trail Marathon", venue=None)
    other["fields"]["name"]["evidence"] = "Vietnam Trail Marathon"
    write_outbox(tmp_path, "h2", other)
    report = run(db, tmp_path)
    assert report.duplicates == 1
    (proposal,) = pending_proposals(db)
    assert "also seen in: blog-b" in (proposal.reason or "")


def test_better_source_replaces_a_weaker_pending_create(db: Session, tmp_path: Path) -> None:
    weak = make_source(db, tier=3, source_id="blog")
    official = make_source(db, tier=2, source_id="official")
    make_document(db, weak, "h1")
    make_document(db, official, "h2")
    write_outbox(tmp_path, "h1", candidate())
    run(db, tmp_path)
    write_outbox(tmp_path, "h2", candidate())
    report = run(db, tmp_path)
    assert report.created == 1
    statuses = sorted(p.status for p in db.scalars(select(ChangeProposal)))
    assert statuses == ["auto_applied", "superseded"]
    assert count(db, Event) == 1


def test_approving_a_create_for_an_event_that_now_exists_is_superseded(
    db: Session, tmp_path: Path
) -> None:
    blog = make_source(db, tier=3, source_id="blog")
    make_document(db, blog, "h1")
    write_outbox(tmp_path, "h1", candidate())
    run(db, tmp_path)
    (proposal,) = pending_proposals(db)
    official = make_source(db, tier=2, source_id="official")
    make_document(db, official, "h2")
    write_outbox(tmp_path, "h2", candidate(name="Vietnam Trail Marathon 2027 "))
    db.refresh(proposal)
    event = Event(
        slug="vietnam-trail-marathon-2027", name="Vietnam Trail Marathon 2027",
        event_type="trail", start_date=date(2027, 1, 16),
    )  # fmt: skip
    db.add(event)
    db.commit()
    assert "superseded" in approve(db, proposal.id, actor="cli")
    assert count(db, Event) == 1


def test_omitted_evidence_keeps_the_value_but_forces_review(db: Session, tmp_path: Path) -> None:
    source = make_source(db)
    make_document(db, source, "h1")
    cand = candidate()
    for name in ("event_type", "province", "venue", "organizer", "distances"):
        cand["fields"].pop(name)
    write_outbox(tmp_path, "h1", cand)
    report = run(db, tmp_path)
    assert (report.created, report.pending) == (0, 1)
    assert any("no quote for" in w for w in report.warnings)
    value = pending_proposals(db)[0].new_value
    assert value["province"] == "Sơn La" and value["event_type"] == "trail"


def test_invented_evidence_on_a_descriptive_field_is_still_dropped(
    db: Session, tmp_path: Path
) -> None:
    source = make_source(db, tier=3, source_id="blog")
    make_document(db, source, "h1")
    cand = candidate()
    cand["fields"]["province"]["evidence"] = "Lâm Đồng, Đà Lạt"
    write_outbox(tmp_path, "h1", cand)
    run(db, tmp_path)
    assert pending_proposals(db)[0].new_value["province"] is None


def test_pending_filters(db: Session, tmp_path: Path) -> None:
    blog = make_source(db, tier=3, source_id="blog")
    other = make_source(db, tier=3, source_id="listing")
    make_document(db, blog, "h1")
    make_document(db, other, "h2", PAGE + "\nDalat Ultra Trail 2027\nLâm Đồng")
    write_outbox(tmp_path, "h1", candidate())
    other_event = candidate(name="Dalat Ultra Trail 2027", province="Lâm Đồng")
    other_event["fields"]["name"]["evidence"] = "Dalat Ultra Trail 2027"
    other_event["fields"]["province"]["evidence"] = "Lâm Đồng"
    write_outbox(tmp_path, "h2", other_event)
    run(db, tmp_path)
    assert len(pending_proposals(db)) == 2
    assert len(pending_proposals(db, source="blog")) == 1
    assert len(pending_proposals(db, kind="update")) == 0
    assert len(pending_proposals(db, min_confidence=0.99)) == 0


def test_finished_events_are_not_added(db: Session, tmp_path: Path) -> None:
    source = make_source(db)
    page = PAGE.replace("16/01/2027", "16/01/2026")
    make_document(db, source, "h1", page)
    past = candidate(start_date="2026-01-16")
    past["fields"]["start_date"]["evidence"] = "Ngày thi đấu: 16/01/2026"
    write_outbox(tmp_path, "h1", past)
    report = run(db, tmp_path)
    assert report.created == 0 and report.pending == 0
    assert any("already finished" in r for r in report.rejected)
    assert count(db, Event) == 0
