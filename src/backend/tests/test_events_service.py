from datetime import date

import pytest
from sqlalchemy.dialects import postgresql

from app.models import Event
from app.services import events as service

TODAY = date(2026, 11, 6)


def _event(**overrides: object) -> Event:
    data: dict[str, object] = {
        "slug": "e",
        "name": "E",
        "event_type": "trail",
        "start_date": date(2027, 1, 16),
        "status": "registration_open",
    }
    data.update(overrides)
    return Event(**data)


def test_cursor_round_trip() -> None:
    cursor = service.encode_cursor(date(2027, 1, 16), 42)
    assert service.decode_cursor(cursor) == (date(2027, 1, 16), 42)


@pytest.mark.parametrize("bad", ["", "not-base64!!", "e30", "eyJkIjogIngifQ"])
def test_decode_cursor_rejects_garbage(bad: str) -> None:
    with pytest.raises(ValueError):
        service.decode_cursor(bad)


def test_cancelled_stays_cancelled_even_if_past() -> None:
    event = _event(status="cancelled", start_date=date(2026, 3, 14))
    assert service.effective_status(event, TODAY) == "cancelled"


def test_past_event_is_completed() -> None:
    event = _event(start_date=date(2026, 10, 1), status="registration_open")
    assert service.effective_status(event, TODAY) == "completed"


def test_multi_day_event_in_progress_is_not_completed() -> None:
    event = _event(start_date=date(2026, 11, 5), end_date=date(2026, 11, 7))
    assert service.effective_status(event, TODAY) == "registration_open"


def test_open_event_past_deadline_is_registration_closed() -> None:
    event = _event(registration_deadline=date(2026, 11, 5))
    assert service.effective_status(event, TODAY) == "registration_closed"
    assert service.days_left(event, TODAY) is None
    assert service.is_closing_soon(event, TODAY) is False


@pytest.mark.parametrize(
    "deadline,expected",
    [
        (date(2026, 11, 6), True),  # today
        (date(2026, 11, 13), True),  # exactly 7 days
        (date(2026, 11, 14), False),  # 8 days
        (None, False),
    ],
)
def test_closing_soon_window(deadline: date | None, expected: bool) -> None:
    assert service.is_closing_soon(_event(registration_deadline=deadline), TODAY) is expected


def test_days_left_counts_calendar_days() -> None:
    assert service.days_left(_event(registration_deadline=date(2026, 12, 31)), TODAY) == 55


def test_search_statement_escapes_wildcards_and_compiles() -> None:
    filters = service.EventFilters(q="100% da_lat", distances=["42", "ultra"], region="south")
    stmt = service.page_statement(filters, TODAY, 20, (date(2027, 1, 1), 5))
    sql = str(stmt.compile(dialect=postgresql.dialect()))
    assert "f_unaccent" in sql
    assert "ESCAPE" in sql
    assert "events.start_date, events.id) >" in sql.replace(
        "(events.start_date", "events.start_date"
    )
    assert service._escape_like("100%_\\") == "100\\%\\_\\\\"
