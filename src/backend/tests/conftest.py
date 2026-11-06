import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from alembic import command
from app.db import SessionLocal, engine

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _refuse_unsafe_database() -> None:
    """The db fixture TRUNCATEs tables: only ever run against a database meant for tests."""
    name = engine.url.database or ""
    if name.endswith("_test") or os.getenv("ALLOW_DB_RESET"):
        return
    message = (
        f"refusing to reset database '{name}': tests truncate tables. Point DATABASE_URL at a "
        "database whose name ends in _test (or set ALLOW_DB_RESET=1 if you really mean it)."
    )
    if os.getenv("REQUIRE_DB"):
        pytest.fail(message)
    pytest.skip(message)


@pytest.fixture(scope="session")
def migrated_db() -> None:
    """Apply migrations to the test database (skip locally if unreachable or not a test DB)."""
    _refuse_unsafe_database()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        if os.getenv("REQUIRE_DB"):
            pytest.fail(f"database required but unreachable: {exc}")
        pytest.skip("PostgreSQL not reachable; set DATABASE_URL (CI sets REQUIRE_DB=1)")
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    command.upgrade(cfg, "head")


@pytest.fixture
def db(migrated_db: None) -> Iterator[Session]:
    with SessionLocal() as session:
        session.execute(
            text(
                "TRUNCATE events, distances, sources, raw_documents, change_proposals, "
                "audit_log RESTART IDENTITY CASCADE"
            )
        )
        session.commit()
        yield session
