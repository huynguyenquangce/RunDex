"""Find candidate page URLs for a source (sitemaps are followed, pages are used as they are)."""

import re
from urllib.parse import urlsplit

from defusedxml import ElementTree

from app.ingest.fetcher import Fetcher
from app.models import Source

MAX_SITEMAP_DEPTH = 2
# Pages that never describe an event.
_NOISE = re.compile(
    r"(/wp-json/|/feed/?$|/tag/|/category/|/author/|/page/\d+|/cart|/checkout|/account|"
    r"\.(jpg|jpeg|png|gif|webp|svg|pdf|css|js|zip)(\?|$))",
    re.IGNORECASE,
)


def parse_sitemap(xml: str) -> tuple[list[str], list[str]]:
    """Return (page_urls, child_sitemap_urls) from a sitemap or sitemap index."""
    try:
        root = ElementTree.fromstring(xml.encode("utf-8"))
    except ElementTree.ParseError:
        return [], []
    pages: list[str] = []
    children: list[str] = []
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag not in ("url", "sitemap"):
            continue
        for child in element:
            if child.tag.rsplit("}", 1)[-1] == "loc" and child.text:
                (pages if tag == "url" else children).append(child.text.strip())
    return pages, children


def discover_urls(source: Source, fetcher: Fetcher, limit: int) -> list[str]:
    """Candidate page URLs for one source, at most `limit`."""
    if source.kind != "sitemap":
        return [source.url]
    include = re.compile(source.url_include) if source.url_include else None
    host = urlsplit(source.url).netloc
    found: list[str] = []
    seen: set[str] = set()
    queue = [(source.url, 0)]
    while queue and len(found) < limit:
        sitemap_url, depth = queue.pop(0)
        if sitemap_url in seen:
            continue
        seen.add(sitemap_url)
        result = fetcher.fetch(sitemap_url)
        if not result.raw:
            continue
        pages, children = parse_sitemap(result.raw)
        if depth < MAX_SITEMAP_DEPTH:
            queue.extend((child, depth + 1) for child in children)
        for page in pages:
            if urlsplit(page).netloc != host or _NOISE.search(page):
                continue
            if include is not None and not include.search(page):
                continue
            if page not in seen:
                seen.add(page)
                found.append(page)
                if len(found) >= limit:
                    break
    return found
