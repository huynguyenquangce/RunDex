"""Polite HTTP fetcher: honest User-Agent, robots.txt, per-host rate limit, conditional GET."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from app.ingest.html_text import extract_text

USER_AGENT = "RunDexBot/0.1 (+https://github.com/huynguyenquangce/RunDex)"
ROBOTS_TOKEN = "RunDexBot"
MAX_BYTES = 2_000_000
TEXT_TYPES = ("text/html", "application/xhtml+xml", "text/xml", "application/xml", "text/plain")


@dataclass
class FetchResult:
    url: str
    status: int | None = None
    text: str | None = None
    raw: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    not_modified: bool = False
    skipped: str | None = None  # reason when nothing was fetched or usable


class Fetcher:
    def __init__(
        self,
        client: httpx.Client,
        delay_seconds: float = 2.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._client = client
        self._delay = delay_seconds
        self._sleep = sleep
        self._clock = clock
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser | None] = {}

    # -- robots.txt ------------------------------------------------------------------------
    def _robots_for(self, host_root: str) -> RobotFileParser | None:
        """None means "do not crawl this host" (robots unavailable in a way that says stop)."""
        if host_root in self._robots:
            return self._robots[host_root]
        parser: RobotFileParser | None
        try:
            self._wait(host_root)
            response = self._client.get(f"{host_root}/robots.txt")
        except httpx.HTTPError:
            parser = None
        else:
            if response.status_code in (404, 410):
                parser = RobotFileParser()
                parser.parse([])
            elif response.status_code == 200:
                parser = RobotFileParser()
                parser.parse(response.text.splitlines())
            else:  # 401/403/5xx: be conservative
                parser = None
        self._robots[host_root] = parser
        return parser

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        parser = self._robots_for(f"{parts.scheme}://{parts.netloc}")
        return parser is not None and parser.can_fetch(ROBOTS_TOKEN, url)

    # -- rate limit ------------------------------------------------------------------------
    def _wait(self, host_root: str) -> None:
        last = self._last_request.get(host_root)
        if last is not None:
            remaining = self._delay - (self._clock() - last)
            if remaining > 0:
                self._sleep(remaining)
        self._last_request[host_root] = self._clock()

    # -- fetch -----------------------------------------------------------------------------
    def fetch(
        self, url: str, etag: str | None = None, last_modified: str | None = None
    ) -> FetchResult:
        if not self.allowed(url):
            return FetchResult(url, skipped="blocked by robots.txt (or robots.txt unavailable)")
        parts = urlsplit(url)
        self._wait(f"{parts.scheme}://{parts.netloc}")
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        try:
            with self._client.stream("GET", url, headers=headers) as response:
                if response.status_code == 304:
                    return FetchResult(url, status=304, not_modified=True)
                if response.status_code != 200:
                    return FetchResult(url, status=response.status_code, skipped="http error")
                content_type = response.headers.get("content-type", "").split(";")[0].strip()
                if content_type and not content_type.startswith(TEXT_TYPES):
                    return FetchResult(url, status=200, skipped=f"unsupported type {content_type}")
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        return FetchResult(url, status=200, skipped="response too large")
                encoding = response.encoding or "utf-8"
                raw = bytes(body).decode(encoding, errors="replace")
                is_html = "html" in content_type or raw.lstrip()[:15].lower().startswith(
                    ("<!doctype html", "<html")
                )
                return FetchResult(
                    url,
                    status=200,
                    raw=raw,
                    text=extract_text(raw) if is_html else raw,
                    etag=response.headers.get("etag"),
                    last_modified=response.headers.get("last-modified"),
                )
        except httpx.HTTPError as exc:
            return FetchResult(url, skipped=f"network error: {type(exc).__name__}")
