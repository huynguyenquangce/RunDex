"""Rule-based extraction of schema.org Event JSON-LD (pace8.vn style) and its verification."""

import json
from datetime import date

from app.ingest.extract import verify_candidate
from app.ingest.html_text import extract_text
from app.ingest.jsonld import extract_jsonld
from app.ingest.normalize import normalize

URL = "https://pace8.vn/su-kien/vietnam-trail-marathon-2027"


def _offer(name: str, price: int, availability: str = "SoldOut") -> dict:
    return {
        "@type": "Offer",
        "name": name,
        "price": price,
        "availability": f"https://schema.org/{availability}",
        "url": URL,
    }


def _event(offers: list[dict] | None = None, **overrides) -> dict:
    offers = offers if offers is not None else [_offer("21Km", 3_300_000, "InStock")]
    return {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": "Vietnam Trail Marathon 2027",
        "startDate": "2027-01-15T00:00:00+07:00",
        "endDate": "2027-01-16T00:00:00+07:00",
        "location": {"@type": "Place", "name": "Mộc Châu, Sơn La"},
        "organizer": {"@type": "Organization", "name": "Topas Group"},
        "url": URL,
        "offers": offers,
    } | overrides


def _page(offers: list[dict], **overrides) -> str:
    event = _event(offers, **overrides)
    org = {"@graph": [{"@type": "Organization", "name": "Pace8"}]}
    html = "".join(
        f'<script type="application/ld+json">{json.dumps(b, ensure_ascii=False)}</script>'
        for b in (event, org)
    )
    return extract_text(f"<html><head><title>VTM</title>{html}</head><body>Hi</body></html>")


def _run(text: str):
    extraction = extract_jsonld(text, "h" * 64, URL)
    assert extraction is not None
    candidate = extraction.candidates[0]
    return candidate, verify_candidate(candidate, text)


def test_reads_event_fields_and_every_quote_is_on_the_page() -> None:
    text = _page([_offer("21Km", 3_300_000, "InStock"), _offer("5Km", 1_700_000, "InStock")])
    _, verified = _run(text)
    assert verified.ok and not verified.dropped and not verified.inferred
    assert not verified.unverified
    data = normalize(verified)
    assert data.name == "Vietnam Trail Marathon 2027"
    assert (data.start_date, data.end_date) == (date(2027, 1, 15), date(2027, 1, 16))
    assert data.province == "Sơn La" and data.venue == "Mộc Châu, Sơn La"
    assert data.organizer == "Topas Group" and data.event_type == "trail"
    assert data.status == "scheduled" and data.registration_url == URL
    assert {d.label: d.fee_vnd for d in data.distances} == {"21K": 3_300_000, "5K": 1_700_000}


def test_all_sold_out_means_registration_closed() -> None:
    _, verified = _run(_page([_offer("21Km", 3_300_000), _offer("10Km", 1_900_000)]))
    assert normalize(verified).status == "registration_closed"


def test_one_ticket_still_on_sale_keeps_the_event_open() -> None:
    _, verified = _run(_page([_offer("21Km", 3_300_000), _offer("10Km", 1_900_000, "InStock")]))
    assert normalize(verified).status == "scheduled"


def test_childrens_ticket_does_not_replace_the_adult_distance() -> None:
    offers = [_offer("5Km Trẻ Em", 1_000_000), _offer("5Km", 1_700_000)]
    _, verified = _run(_page(offers))
    assert {d.label: d.fee_vnd for d in normalize(verified).distances} == {"5K": 1_700_000}


def test_no_event_or_no_start_date_gives_nothing() -> None:
    plain = extract_text("<html><title>x</title><body>no data</body></html>")
    assert extract_jsonld(plain, "h" * 64, URL) is None
    assert extract_jsonld(_page([], startDate="soon"), "h" * 64, URL) is None


def test_road_event_has_no_guessed_type() -> None:
    _, verified = _run(_page([_offer("42Km", 1_000_000)], name="HCMC Marathon 2027"))
    assert normalize(verified).event_type is None


# ---- end to end (database): fetch -> outbox -> apply ------------------------------------


def test_jsonld_source_goes_fetch_to_catalog_without_ai(db, tmp_path) -> None:  # type: ignore[no-untyped-def]
    import httpx
    from sqlalchemy import select

    from app.ingest.fetch_service import fetch_source
    from app.ingest.pipeline import process_outbox
    from app.models import ChangeProposal, Event, Source
    from tests.test_ingest_fetch import html_response, make_fetcher

    page = f"<html><script type='application/ld+json'>{json.dumps(_event())}</script></html>"
    routes = {
        "https://pace8.vn/robots.txt": httpx.Response(404),
        URL: lambda request: html_response(page),
    }
    fetcher, _, _ = make_fetcher(routes)
    source = Source(
        id="pace8", name="Pace8", kind="event_page", url=URL, tier=2, extractor="jsonld"
    )
    db.add(source)
    db.commit()
    today = date(2026, 11, 11)

    fetch_source(db, source, fetcher, limit=5, data_dir=tmp_path)
    assert not list((tmp_path / "inbox").glob("*.json"))  # no AI step needed
    report = process_outbox(db, data_dir=tmp_path, today=today)
    assert report.errors == [] and report.candidates == 1
    event = db.scalars(select(Event)).one()
    assert event.name == "Vietnam Trail Marathon 2027"
    assert [d.fee_vnd for d in event.distances] == [3_300_000]

    # Sold out later: the status change is high impact, so a person decides (tier 2).
    sold_out = _event(offers=[_offer("21Km", 3_300_000)])
    page = f"<html><script type='application/ld+json'>{json.dumps(sold_out)}</script></html>"
    fetch_source(db, source, fetcher, limit=5, data_dir=tmp_path)
    process_outbox(db, data_dir=tmp_path, today=today)
    proposal = db.scalars(select(ChangeProposal).where(ChangeProposal.status == "pending")).one()
    assert (proposal.field, proposal.new_value) == ("status", "registration_closed")
