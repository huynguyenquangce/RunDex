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


@pytest.fixture(scope="session")
def migrated_db() -> None:
    """Apply migrations to the configured database (skip locally if unreachable)."""
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
        session.execute(text("TRUNCATE events, distances RESTART IDENTITY CASCADE"))
        session.commit()
        yield session
