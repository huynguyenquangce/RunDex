"""Deterministic extractor for pages that publish a schema.org `Event` as JSON-LD (e.g. pace8.vn).

No AI is involved: values are read from the structured data and every one is quoted from the
JSON-LD text of the page, so the normal verify step still proves the value is really on the page.
Fields the page does not state (start time, elevation, cut-off, deadline) are left empty.
"""

import json
import re
from datetime import date

from app.ingest.extract import DistanceCandidate, EventCandidate, Evidence, Extraction

_MARKER = "JSON-LD:\n"
_CONFIDENCE = 0.95
_PLAIN_DISTANCE = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*km\s*$", re.IGNORECASE)
_TRAIL_WORDS = re.compile(r"\b(trail|mountain|jungle|ultra)\b", re.IGNORECASE)


def _events(text: str) -> list[dict]:
    """Event objects found in the JSON-LD section of a fetched page text."""
    if _MARKER not in text:
        return []
    found: list[dict] = []
    for line in text.split(_MARKER, 1)[1].split("\n"):
        try:
            block = json.loads(line)
        except ValueError:
            continue
        nodes = block.get("@graph", [block]) if isinstance(block, dict) else []
        found += [n for n in nodes if isinstance(n, dict) and "Event" in str(n.get("@type"))]
    return found


def _quote(key: str, value: object) -> str:
    """The `"key": value` text exactly as the page text spells it."""
    return f"{json.dumps(key, ensure_ascii=False)}: {json.dumps(value, ensure_ascii=False)}"


def _day(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _candidate(event: dict) -> EventCandidate | None:
    name, start = event.get("name"), _day(event.get("startDate"))
    if not isinstance(name, str) or start is None:
        return None
    candidate = EventCandidate(name=name, start_date=start)

    def cite(field: str, key: str, value: object) -> None:
        candidate.fields[field] = Evidence(confidence=_CONFIDENCE, evidence=_quote(key, value))

    cite("name", "name", name)
    cite("start_date", "startDate", event["startDate"])
    end = _day(event.get("endDate"))
    if end is not None:
        candidate.end_date = end
        cite("end_date", "endDate", event["endDate"])

    place = event.get("location")
    place_name = place.get("name") if isinstance(place, dict) else None
    if isinstance(place_name, str) and place_name.strip():
        candidate.venue = place_name.strip()
        candidate.province = place_name.rsplit(",", 1)[-1].strip()
        cite("venue", "name", place_name)
        cite("province", "name", place_name)
    organizer = event.get("organizer")
    if isinstance(organizer, dict) and isinstance(organizer.get("name"), str):
        candidate.organizer = organizer["name"]
        cite("organizer", "name", organizer["name"])
    if _TRAIL_WORDS.search(name):
        candidate.event_type = "trail"
        cite("event_type", "name", name)

    offers = [o for o in event.get("offers") or [] if isinstance(o, dict)]
    for offer in offers:
        label = offer.get("name")
        if not isinstance(label, str) or not _PLAIN_DISTANCE.match(label):
            continue  # e.g. a children's 5Km ticket must not replace the adult 5Km
        if any(d.label.lower() == label.lower() for d in candidate.distances):
            continue
        price = offer.get("price")
        candidate.distances.append(
            DistanceCandidate(
                label=label.strip(),
                distance_km=float(_PLAIN_DISTANCE.match(label).group(1).replace(",", ".")),
                fee_vnd=int(price) if isinstance(price, int | float) and price > 0 else None,
            )
        )
    if candidate.distances:
        first = next(o for o in offers if o.get("name") == candidate.distances[0].label)
        cite("distances", "name", first["name"])
    if offers and all(str(o.get("availability", "")).endswith("SoldOut") for o in offers):
        candidate.status = "registration_closed"
        cite("status", "availability", offers[0]["availability"])
    url = event.get("url")
    if isinstance(url, str) and url.startswith("http"):
        candidate.registration_url = url
        cite("registration_url", "url", url)
    return candidate


def extract_jsonld(text: str, content_hash: str, source_url: str) -> Extraction | None:
    """An Extraction for the page, or None when it has no usable schema.org Event."""
    candidates = [c for e in _events(text) if (c := _candidate(e)) is not None]
    if not candidates:
        return None
    return Extraction(content_hash=content_hash, source_url=source_url, candidates=candidates)
