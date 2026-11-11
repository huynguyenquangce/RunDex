"""Source registry: validate config/sources.yaml and sync it into the `sources` table."""

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, HttpUrl, field_validator
from sqlalchemy.orm import Session

from app.models import Source

DEFAULT_SOURCES_PATH = Path(__file__).resolve().parents[2] / "config" / "sources.yaml"


class SourceConfig(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=80)
    name: str
    kind: Literal["sitemap", "listing_page", "event_page"]
    url: HttpUrl
    tier: Literal[1, 2, 3]
    url_include: str | None = None
    enabled: bool = True
    refresh_days: int = Field(default=7, gt=0)
    # "jsonld": read schema.org Event data by rules (no AI); pages without it fall back to "ai".
    extractor: Literal["ai", "jsonld"] = "ai"
    notes: str | None = None

    @field_validator("url_include")
    @classmethod
    def _regex_compiles(cls, value: str | None) -> str | None:
        if value is not None:
            re.compile(value)
        return value


def load_sources(path: Path = DEFAULT_SOURCES_PATH) -> list[SourceConfig]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    configs = [SourceConfig.model_validate(item) for item in raw.get("sources", [])]
    ids = [c.id for c in configs]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source id in sources.yaml")
    return configs


def sync_sources(session: Session, configs: list[SourceConfig]) -> tuple[int, int]:
    """Upsert the registry into the database. Returns (created, updated)."""
    created = updated = 0
    for config in configs:
        source = session.get(Source, config.id)
        if source is None:
            source = Source(id=config.id)
            session.add(source)
            created += 1
        else:
            updated += 1
        source.name = config.name
        source.kind = config.kind
        source.url = str(config.url)
        source.tier = config.tier
        source.url_include = config.url_include
        source.enabled = config.enabled
        source.refresh_days = config.refresh_days
        source.extractor = config.extractor
        source.notes = config.notes
    session.commit()
    return created, updated
