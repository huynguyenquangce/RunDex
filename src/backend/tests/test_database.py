from datetime import date

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Distance, Event
from app.seed import DEFAULT_SEED_PATH, load_seed_file, seed_events


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
    events = load_seed_file(DEFAULT_SEED_PATH)
    created, updated = seed_events(db, events)
    assert (created, updated) == (len(events), 0)
    count = db.scalar(text("SELECT count(*) FROM events"))
    distances = db.scalar(text("SELECT count(*) FROM distances"))

    created, updated = seed_events(db, events)
    assert (created, updated) == (0, len(events))
    assert db.scalar(text("SELECT count(*) FROM events")) == count
    assert db.scalar(text("SELECT count(*) FROM distances")) == distances
