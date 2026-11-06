from collections.abc import Iterator
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.db import SessionLocal

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


def get_today() -> date:
    """Today's date in Vietnam (overridable in tests)."""
    return datetime.now(VIETNAM_TZ).date()
