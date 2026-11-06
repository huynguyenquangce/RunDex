import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingest.discover import discover_urls, parse_sitemap
from app.ingest.fetch_service import content_hash, fetch_source
from app.ingest.fetcher import Fetcher
from app.ingest.html_text import extract_text
from app.models import RawDocument, Source

HTML = """<html><head><title>Giải chạy Test 2027</title>
<script type="application/ld+json">
{"@type": "SportsEvent", "name": "Test Run", "startDate": "2027-02-01"}
</script>
<style>.x { color: red }</style></head>
<body><nav>Menu</nav><h1>Test Run 2027</h1><p>Ngày 01/02/2027 tại Đà Lạt</p>
<script>var secret = 1;</script><ul><li>21K</li><li>42K</li></ul></body></html>"""

SITEMAP_INDEX = """<?xml version="1.0"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.org/events-sitemap.xml</loc></sitemap>
  <sitemap><loc>https://example.org/other-sitemap.xml</loc></sitemap>
</sitemapindex>"""
EVENTS_SITEMAP = """<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.org/events/run-a/</loc></url>
  <url><loc>https://example.org/events/run-b/</loc></url>
  <url><loc>https://example.org/events/logo.png</loc></url>
  <url><loc>https://elsewhere.org/events/run-c/</loc></url>
  <url><loc>https://example.org/about/</loc></url>
</urlset>"""
OTHER_SITEMAP = """<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.org/events/run-d/</loc></url>
</urlset>"""


def make_fetcher(routes: dict[str, httpx.Response | tuple], delay: float = 0.0):
    """Build a Fetcher on a mock transport. `routes` maps URL -> Response or callable."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        route = routes.get(str(request.url))
        if route is None:
            return httpx.Response(404)
        return route(request) if callable(route) else route

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    sleeps: list[float] = []
    now = [0.0]
    fetcher = Fetcher(client, delay_seconds=delay, sleep=sleeps.append, clock=lambda: now[0])
    return fetcher, requests, sleeps


def html_response(body: str = HTML, **headers: str) -> httpx.Response:
    return httpx.Response(200, text=body, headers={"content-type": "text/html", **headers})


# ---- text extraction ---------------------------------------------------------------------


def test_extract_text_keeps_visible_text_title_and_jsonld() -> None:
    text = extract_text(HTML)
    assert "TITLE: Giải chạy Test 2027" in text
    assert "Ngày 01/02/2027 tại Đà Lạt" in text
    assert "21K" in text and "42K" in text
    assert "secret" not in text and "color: red" not in text
    assert 'JSON-LD:\n{"@type": "SportsEvent"' in text


# ---- sitemap parsing and discovery -------------------------------------------------------


def test_parse_sitemap_index_and_urlset() -> None:
    pages, children = parse_sitemap(SITEMAP_INDEX)
    assert pages == [] and len(children) == 2
    pages, children = parse_sitemap(EVENTS_SITEMAP)
    assert len(pages) == 5 and children == []
    assert parse_sitemap("<not xml") == ([], [])


def test_discover_follows_index_filters_and_limits() -> None:
    routes = {
        "https://example.org/robots.txt": httpx.Response(200, text="User-agent: *\nAllow: /"),
        "https://example.org/sitemap.xml": httpx.Response(200, text=SITEMAP_INDEX),
        "https://example.org/events-sitemap.xml": httpx.Response(200, text=EVENTS_SITEMAP),
        "https://example.org/other-sitemap.xml": httpx.Response(200, text=OTHER_SITEMAP),
    }
    fetcher, _, _ = make_fetcher(routes)
    source = Source(
        id="s", name="S", kind="sitemap", url="https://example.org/sitemap.xml", tier=2,
        url_include="/events/", enabled=True, refresh_days=7,
    )  # fmt: skip
    urls = discover_urls(source, fetcher, limit=10)
    assert urls == [
        "https://example.org/events/run-a/",
        "https://example.org/events/run-b/",
        "https://example.org/events/run-d/",
    ]  # other host, image and /about/ are dropped
    assert len(discover_urls(source, fetcher, limit=2)) == 2


def test_discover_returns_the_page_itself_for_non_sitemaps() -> None:
    fetcher, requests, _ = make_fetcher({})
    source = Source(id="p", name="P", kind="event_page", url="https://example.org/e/", tier=2)
    assert discover_urls(source, fetcher, limit=5) == ["https://example.org/e/"]
    assert requests == []


# ---- politeness --------------------------------------------------------------------------


def test_robots_disallow_blocks_fetch() -> None:
    routes = {
        "https://example.org/robots.txt": httpx.Response(
            200, text="User-agent: *\nDisallow: /private/"
        ),
        "https://example.org/private/x": html_response(),
        "https://example.org/public/x": html_response(),
    }
    fetcher, requests, _ = make_fetcher(routes)
    blocked = fetcher.fetch("https://example.org/private/x")
    assert blocked.skipped and "robots" in blocked.skipped
    assert fetcher.fetch("https://example.org/public/x").text is not None
    assert all("private" not in str(r.url) for r in requests)


def test_named_bot_rule_applies() -> None:
    routes = {
        "https://example.org/robots.txt": httpx.Response(
            200, text="User-agent: RunDexBot\nDisallow: /\n\nUser-agent: *\nAllow: /"
        ),
        "https://example.org/a": html_response(),
    }
    fetcher, _, _ = make_fetcher(routes)
    assert fetcher.fetch("https://example.org/a").skipped


@pytest.mark.parametrize("status,allowed", [(404, True), (403, False), (500, False)])
def test_robots_unavailable_policy(status: int, allowed: bool) -> None:
    routes = {
        "https://example.org/robots.txt": httpx.Response(status),
        "https://example.org/a": html_response(),
    }
    fetcher, _, _ = make_fetcher(routes)
    assert (fetcher.fetch("https://example.org/a").text is not None) is allowed


def test_rate_limit_waits_between_requests_to_the_same_host() -> None:
    routes = {
        "https://example.org/robots.txt": httpx.Response(404),
        "https://example.org/a": html_response(),
        "https://example.org/b": html_response(),
    }
    fetcher, _, sleeps = make_fetcher(routes, delay=2.0)
    fetcher.fetch("https://example.org/a")
    fetcher.fetch("https://example.org/b")
    assert sleeps and all(s == pytest.approx(2.0) for s in sleeps)


def test_conditional_get_returns_not_modified() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("if-none-match") == '"v1"':
            return httpx.Response(304)
        return html_response(etag='"v1"')

    routes = {
        "https://example.org/robots.txt": httpx.Response(404),
        "https://example.org/a": handler,
    }
    fetcher, _, _ = make_fetcher(routes)
    first = fetcher.fetch("https://example.org/a")
    assert first.etag == '"v1"'
    assert fetcher.fetch("https://example.org/a", etag=first.etag).not_modified


def test_non_text_and_oversized_responses_are_skipped() -> None:
    routes = {
        "https://example.org/robots.txt": httpx.Response(404),
        "https://example.org/pic": httpx.Response(
            200, content=b"x", headers={"content-type": "image/png"}
        ),
        "https://example.org/big": httpx.Response(
            200, content=b"a" * 2_100_000, headers={"content-type": "text/html"}
        ),
    }
    fetcher, _, _ = make_fetcher(routes)
    assert "unsupported" in (fetcher.fetch("https://example.org/pic").skipped or "")
    assert "large" in (fetcher.fetch("https://example.org/big").skipped or "")


# ---- fetch service (database) ------------------------------------------------------------


def test_fetch_source_queues_new_and_changed_pages_only(db: Session, tmp_path: Path) -> None:
    state = {"body": HTML}
    routes = {
        "https://example.org/robots.txt": httpx.Response(404),
        "https://example.org/event": lambda request: html_response(state["body"]),
    }
    fetcher, _, _ = make_fetcher(routes)
    source = Source(id="s", name="S", kind="event_page", url="https://example.org/event", tier=2)
    db.add(source)
    db.commit()
    now = datetime(2026, 11, 6, tzinfo=UTC)

    report = fetch_source(db, source, fetcher, limit=5, data_dir=tmp_path, now=now)
    assert (report.new_or_changed, report.unchanged) == (1, 0)
    inbox = list((tmp_path / "inbox").glob("*.json"))
    assert len(inbox) == 1
    payload = json.loads(inbox[0].read_text(encoding="utf-8"))
    assert payload["url"] == "https://example.org/event"
    text = (tmp_path / "inbox" / payload["text_file"]).read_text(encoding="utf-8")
    assert payload["content_hash"] == content_hash(extract_text(HTML))
    assert "Đà Lạt" in text

    report = fetch_source(db, source, fetcher, limit=5, data_dir=tmp_path, now=now)
    assert (report.new_or_changed, report.unchanged) == (0, 1)
    assert len(list((tmp_path / "inbox").glob("*.json"))) == 1

    state["body"] = HTML.replace("42K", "50K")
    report = fetch_source(db, source, fetcher, limit=5, data_dir=tmp_path, now=now)
    assert report.new_or_changed == 1
    assert len(list((tmp_path / "inbox").glob("*.json"))) == 2
    assert len(list((tmp_path / "inbox").glob("*.txt"))) == 2
    assert len(db.scalars(select(RawDocument)).all()) == 2
    assert source.last_fetched_at == now


def test_already_extracted_pages_are_not_queued_again(db: Session, tmp_path: Path) -> None:
    routes = {
        "https://example.org/robots.txt": httpx.Response(404),
        "https://example.org/event": html_response(),
    }
    fetcher, _, _ = make_fetcher(routes)
    source = Source(id="s", name="S", kind="event_page", url="https://example.org/event", tier=2)
    db.add(source)
    db.commit()
    digest = content_hash(extract_text(HTML))
    (tmp_path / "outbox").mkdir()
    (tmp_path / "outbox" / f"{digest}.json").write_text("{}", encoding="utf-8")

    fetch_source(db, source, fetcher, limit=5, data_dir=tmp_path)
    assert not list((tmp_path / "inbox").glob("*.json")) if (tmp_path / "inbox").exists() else True


def test_wrap_for_reading_only_changes_whitespace() -> None:
    from app.ingest.fetch_service import wrap_for_reading

    long_line = " ".join(["từ"] * 500)
    wrapped = wrap_for_reading("ngắn\n" + long_line)
    assert max(len(line) for line in wrapped.split("\n")) <= 400
    assert " ".join(wrapped.split()) == " ".join(("ngắn " + long_line).split())


def test_pages_waiting_for_extraction(tmp_path: Path) -> None:
    from app.ingest.fetch_service import pages_waiting_for_extraction

    assert pages_waiting_for_extraction(tmp_path) == []
    (tmp_path / "inbox").mkdir()
    for name in ("a", "b", "c"):
        (tmp_path / "inbox" / f"{name}.json").write_text("{}", encoding="utf-8")
    (tmp_path / "outbox").mkdir()
    (tmp_path / "outbox" / "b.json").write_text("{}", encoding="utf-8")
    assert pages_waiting_for_extraction(tmp_path) == ["a", "c"]
