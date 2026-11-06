"""Read extractor output (data/outbox) and verify it against the page it came from.

The extractor (an LLM) must quote its evidence verbatim. A field whose quote does not occur in
the page text is dropped, so an invented value never reaches the catalog.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field

# Fields that need verified evidence to be kept.
EVIDENCE_FIELDS = (
    "name",
    "organizer",
    "event_type",
    "start_date",
    "end_date",
    "province",
    "venue",
    "status",
    "registration_url",
    "registration_deadline",
    "distances",
)
REQUIRED_FIELDS = ("name", "start_date")
MIN_QUOTE_CHARS = 3


class _Loose(BaseModel):
    model_config = ConfigDict(extra="ignore")


class Evidence(_Loose):
    confidence: float = Field(ge=0, le=1)
    evidence: str


class DistanceCandidate(_Loose):
    label: str
    distance_km: float | None = None
    start_time: time | None = None
    fee_vnd: int | None = None
    elevation_gain_m: int | None = None
    cutoff_minutes: int | None = None
    registration_deadline: date | None = None


class EventCandidate(_Loose):
    name: str | None = None
    organizer: str | None = None
    event_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    province: str | None = None
    venue: str | None = None
    status: str | None = None
    registration_url: str | None = None
    registration_deadline: date | None = None
    distances: list[DistanceCandidate] = Field(default_factory=list)
    fields: dict[str, Evidence] = Field(default_factory=dict)


class Extraction(_Loose):
    content_hash: str
    source_url: str
    candidates: list[EventCandidate] = Field(default_factory=list)


@dataclass
class VerifiedCandidate:
    candidate: EventCandidate
    confidence: dict[str, float] = field(default_factory=dict)
    dropped: list[str] = field(default_factory=list)
    reason: str | None = None  # set when the candidate must be rejected

    @property
    def ok(self) -> bool:
        return self.reason is None

    @property
    def creation_confidence(self) -> float:
        return min(self.confidence.get(f, 0.0) for f in REQUIRED_FIELDS)


def normalize_for_match(text: str) -> str:
    """NFC, collapsed whitespace, case-insensitive: tolerant of layout, strict on characters."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip().casefold()


def verify_candidate(candidate: EventCandidate, page_text: str) -> VerifiedCandidate:
    haystack = normalize_for_match(page_text)
    verified = VerifiedCandidate(candidate=candidate.model_copy(deep=True))
    target = verified.candidate
    for name in EVIDENCE_FIELDS:
        value = getattr(target, name)
        if value in (None, "", []):
            continue
        evidence = candidate.fields.get(name)
        quote = normalize_for_match(evidence.evidence) if evidence else ""
        if evidence and len(quote) >= MIN_QUOTE_CHARS and quote in haystack:
            verified.confidence[name] = evidence.confidence
        else:
            setattr(target, name, [] if name == "distances" else None)
            verified.dropped.append(name)
    missing = [f for f in REQUIRED_FIELDS if getattr(target, f) is None]
    if missing:
        verified.reason = "required field(s) without verified evidence: " + ", ".join(missing)
    return verified
