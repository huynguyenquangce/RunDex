from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Distance, Event
from app.seed import load_seed_file, seed_events

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "events.fixture.yaml"


def _event(**overrides: object) -> Event:
    data: dict[str, object] = {
        "slug": "test-event",
        "name": "Test Event",
        "event_type": "trail",
        "start_date": date(2027, 1, 1),
    }
    data.update(overrides)
    return Event(**data)


def test_tables_exist(db: Session) -> None:
    tables = set(inspect(db.get_bind()).get_table_names())
    assert {"events", "distances"} <= tables


def test_unaccent_handles_vietnamese(db: Session) -> None:
    assert db.scalar(text("SELECT lower(f_unaccent('Đà Lạt, Mộc Châu'))")) == "da lat, moc chau"


def test_search_text_is_generated_without_diacritics(db: Session) -> None:
    db.add(
        _event(
            name="Dalat Ultra Trail", province="Lâm Đồng", venue="Mộc Châu", organizer="Đà Lạt Club"
        )
    )
    db.commit()
    stored = db.scalar(select(Event.search_text))
    assert stored is not None
    assert "lam dong" in stored
    assert "da lat club" in stored
    assert "moc chau" in stored


@pytest.mark.parametrize("field,value", [("event_type", "swim"), ("status", "unknown")])
def test_check_constraints_reject_invalid_values(db: Session, field: str, value: str) -> None:
    db.add(_event(**{field: value}))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_end_date_cannot_precede_start_date(db: Session) -> None:
    db.add(_event(start_date=date(2027, 1, 10), end_date=date(2027, 1, 9)))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_deleting_event_cascades_to_distances(db: Session) -> None:
    event = _event()
    event.distances = [Distance(label="21K", distance_km=21)]
    db.add(event)
    db.commit()
    db.delete(event)
    db.commit()
    assert db.scalar(text("SELECT count(*) FROM distances")) == 0


def test_seed_is_idempotent(db: Session) -> None:
    events = load_seed_file(FIXTURE_PATH)
    created, updated = seed_events(db, events)
    assert (created, updated) == (len(events), 0)
    count = db.scalar(text("SELECT count(*) FROM events"))
    distances = db.scalar(text("SELECT count(*) FROM distances"))

    created, updated = seed_events(db, events)
    assert (created, updated) == (0, len(events))
    assert db.scalar(text("SELECT count(*) FROM events")) == count
    assert db.scalar(text("SELECT count(*) FROM distances")) == distances


def test_ingestion_tables_exist(db: Session) -> None:
    tables = set(inspect(db.get_bind()).get_table_names())
    assert {"sources", "raw_documents", "change_proposals", "audit_log"} <= tables


def test_sync_sources_is_idempotent(db: Session) -> None:
    from app.ingest.sources import DEFAULT_SOURCES_PATH, load_sources, sync_sources

    configs = load_sources(DEFAULT_SOURCES_PATH)
    assert sync_sources(db, configs) == (len(configs), 0)
    assert sync_sources(db, configs) == (0, len(configs))
    assert db.scalar(text("SELECT count(*) FROM sources")) == len(configs)
    disabled = db.scalar(text("SELECT count(*) FROM sources WHERE NOT enabled"))
    assert disabled == sum(1 for c in configs if not c.enabled)


def test_change_proposal_checks_reject_bad_status(db: Session) -> None:
    from app.models import ChangeProposal, Source

    db.add(Source(id="s", name="S", kind="event_page", url="https://example.org", tier=2))
    db.commit()
    db.add(ChangeProposal(kind="create", source_id="s", new_value={}, tier=2, status="maybe"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_catalog_export_round_trips_through_the_seed_loader(db: Session, tmp_path: Path) -> None:
    from app.ingest.export import catalog_yaml

    original = load_seed_file(FIXTURE_PATH)
    seed_events(db, original)
    out = tmp_path / "snapshot.yaml"
    out.write_text(catalog_yaml(db), encoding="utf-8")

    reloaded = load_seed_file(out)  # validates every field through the seed schema
    assert {e.slug for e in reloaded} == {e.slug for e in original}
    by_slug = {e.slug: e for e in reloaded}
    for event in original:
        again = by_slug[event.slug]
        assert (again.name, again.start_date, again.status) == (
            event.name,
            event.start_date,
            event.status,
        )
        assert [d.label for d in again.distances] == [d.label for d in event.distances]
        assert str(again.registration_url) == str(event.registration_url)

    db.execute(text("TRUNCATE events, distances RESTART IDENTITY CASCADE"))
    db.commit()
    db.expunge_all()  # forget the objects of the truncated rows
    created, _ = seed_events(db, reloaded)
    assert created == len(original)
