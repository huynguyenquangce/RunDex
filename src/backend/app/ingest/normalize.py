"""Normalize verified candidates into the catalog's conventions."""

import re
import unicodedata
from datetime import date, time

from pydantic import BaseModel

from app.core.regions import REGIONS
from app.ingest.extract import VerifiedCandidate

EVENT_TYPES = {"road", "trail", "mixed"}
STATUSES = {
    "scheduled",
    "registration_open",
    "registration_closed",
    "postponed",
    "cancelled",
    "completed",
}
# Canonical distances: (low, high) km -> (label, km) so 42.195 and 42 both become 42K / 42.2.
_STANDARD = [(42.0, 42.3, "42K", 42.2), (21.0, 21.2, "21K", 21.1)]
# Keys are folded and punctuation-free (see _key).
_ALIASES = {
    "tp hcm": "TP. Hồ Chí Minh",
    "tphcm": "TP. Hồ Chí Minh",
    "sai gon": "TP. Hồ Chí Minh",
    "ho chi minh": "TP. Hồ Chí Minh",
    "tp ho chi minh": "TP. Hồ Chí Minh",
    "thanh pho ho chi minh": "TP. Hồ Chí Minh",
    "ha noi": "Hà Nội",
    "hue": "Huế",
}


class DistanceData(BaseModel):
    label: str
    distance_km: float
    start_time: time | None = None
    fee_vnd: int | None = None
    elevation_gain_m: int | None = None
    cutoff_minutes: int | None = None
    registration_deadline: date | None = None


class EventData(BaseModel):
    slug: str
    name: str
    organizer: str | None = None
    event_type: str | None = None
    start_date: date
    end_date: date | None = None
    province: str | None = None
    venue: str | None = None
    status: str = "scheduled"
    registration_url: str | None = None
    registration_deadline: date | None = None
    distances: list[DistanceData] = []


def fold(text: str) -> str:
    """Lowercase ASCII form: 'Đà Lạt' -> 'da lat'."""
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower().strip()


def slugify(name: str, year: int) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", fold(name)).strip("-")
    return base if str(year) in base else f"{base}-{year}"


def _key(text: str) -> str:
    return re.sub(r"[.\s]+", " ", fold(text)).strip()


def normalize_province(value: str | None) -> str | None:
    if not value:
        return None
    key = _key(value).removeprefix("tinh ").strip()
    if key in _ALIASES:
        return _ALIASES[key]
    for provinces in REGIONS.values():
        for province in provinces:
            if _key(province) == key:
                return province
    return value.strip()


def normalize_distance(label: str, km: float | None) -> tuple[str, float] | None:
    if km is None:
        match = re.search(r"(\d+(?:[.,]\d+)?)", label)
        if match is None:
            return None
        km = float(match.group(1).replace(",", "."))
    for low, high, std_label, std_km in _STANDARD:
        if low <= km <= high:
            return std_label, std_km
    if km <= 0:
        return None
    rounded = round(km, 2)
    text = f"{rounded:g}"
    return f"{text}K", rounded


def normalize(verified: VerifiedCandidate) -> EventData:
    c = verified.candidate
    assert c.name is not None and c.start_date is not None
    distances: dict[str, DistanceData] = {}
    for d in c.distances:
        normalized = normalize_distance(d.label, d.distance_km)
        if normalized is None:
            continue
        label, km = normalized
        distances.setdefault(
            label,
            DistanceData(
                label=label,
                distance_km=km,
                start_time=d.start_time,
                fee_vnd=d.fee_vnd,
                elevation_gain_m=d.elevation_gain_m,
                cutoff_minutes=d.cutoff_minutes,
                registration_deadline=d.registration_deadline,
            ),
        )
    event_type = (c.event_type or "").strip().lower()
    status = (c.status or "scheduled").strip().lower()
    return EventData(
        slug=slugify(c.name, c.start_date.year),
        name=re.sub(r"\s+", " ", c.name).strip(),
        organizer=c.organizer.strip() if c.organizer else None,
        event_type=event_type if event_type in EVENT_TYPES else None,
        start_date=c.start_date,
        end_date=c.end_date,
        province=normalize_province(c.province),
        venue=c.venue.strip() if c.venue else None,
        status=status if status in STATUSES else "scheduled",
        registration_url=c.registration_url.strip() if c.registration_url else None,
        registration_deadline=c.registration_deadline,
        distances=sorted(distances.values(), key=lambda d: -d.distance_km),
    )
