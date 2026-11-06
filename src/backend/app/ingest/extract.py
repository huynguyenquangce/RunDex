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
# Descriptive fields: when the extractor omits the quote we keep the value but mark it unverified
# (a person must confirm it). A quote that is not on the page is still treated as invention.
DESCRIPTIVE_FIELDS = ("organizer", "event_type", "province", "venue", "distances")
UNVERIFIED_CONFIDENCE = 0.5
DATE_FIELDS = ("start_date", "end_date", "registration_deadline")
# A date whose year the quote does not state was inferred, so it can never be auto-applied.
INFERRED_CONFIDENCE_CAP = 0.6
_MONTH_NAMES = {
    1: ("jan", "january"), 2: ("feb", "february"), 3: ("mar", "march"), 4: ("apr", "april"),
    5: ("may",), 6: ("jun", "june"), 7: ("jul", "july"), 8: ("aug", "august"),
    9: ("sep", "sept", "september"), 10: ("oct", "october"), 11: ("nov", "november"),
    12: ("dec", "december"),
}  # fmt: skip


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
    unverified: list[str] = field(default_factory=list)  # kept, but no quote was given
    inferred: list[str] = field(default_factory=list)  # dates whose year the quote does not state
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


def check_date_against_quote(value: date, quote: str) -> tuple[bool, bool]:
    """Return (consistent, year_stated): does the quote really contain this day and month (and
    not a different year)?"""
    numbers = [int(n) for n in re.findall(r"\d+", quote)]
    words = set(re.findall(r"[a-z]+", normalize_for_match(quote)))
    has_day = value.day in numbers
    has_month = value.month in numbers or any(w in words for w in _MONTH_NAMES[value.month])
    years = [n for n in numbers if 1900 <= n <= 2100]
    year_stated = value.year in years
    if years and not year_stated:
        return False, False  # the quote names a different year
    return has_day and has_month, year_stated


def verify_candidate(candidate: EventCandidate, page_text: str) -> VerifiedCandidate:
    haystack = normalize_for_match(page_text)
    verified = VerifiedCandidate(candidate=candidate.model_copy(deep=True))
    target = verified.candidate
    for name in EVIDENCE_FIELDS:
        value = getattr(target, name)
        if value in (None, "", []):
            continue
        evidence = candidate.fields.get(name)
        if evidence is None and name in DESCRIPTIVE_FIELDS:
            verified.confidence[name] = UNVERIFIED_CONFIDENCE
            verified.unverified.append(name)
            continue
        quote = normalize_for_match(evidence.evidence) if evidence else ""
        if evidence and len(quote) >= MIN_QUOTE_CHARS and quote in haystack:
            confidence = evidence.confidence
            if name in DATE_FIELDS:
                consistent, year_stated = check_date_against_quote(value, evidence.evidence)
                if not consistent:
                    setattr(target, name, None)
                    verified.dropped.append(name)
                    continue
                if not year_stated:
                    confidence = min(confidence, INFERRED_CONFIDENCE_CAP)
                    verified.inferred.append(name)
            verified.confidence[name] = confidence
        else:
            setattr(target, name, [] if name == "distances" else None)
            verified.dropped.append(name)
    missing = [f for f in REQUIRED_FIELDS if getattr(target, f) is None]
    if missing:
        verified.reason = "required field(s) without verified evidence: " + ", ".join(missing)
    return verified
