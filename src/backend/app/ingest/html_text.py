"""Turn an HTML page into plain text for extraction (title, visible text, JSON-LD blocks)."""

import json
import re
from html.parser import HTMLParser

MAX_TEXT_CHARS = 60_000
_SKIP = {"script", "style", "noscript", "svg", "template", "iframe"}
_BLOCK = {
    "p", "div", "br", "li", "ul", "ol", "tr", "table", "section", "article", "header",
    "footer", "nav", "main", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "dd", "dt",
}  # fmt: skip


class _Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.parts: list[str] = []
        self.jsonld: list[str] = []
        self._skip_depth = 0
        self._in_title = False
        self._capture_jsonld = False
        self._jsonld_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self._capture_jsonld = True
            self._jsonld_buf = []
        elif tag in _SKIP:
            self._skip_depth += 1
        if tag in _BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._capture_jsonld:
            self._capture_jsonld = False
            self.jsonld.append("".join(self._jsonld_buf).strip())
        elif tag in _SKIP and self._skip_depth:
            self._skip_depth -= 1
        if tag in _BLOCK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._capture_jsonld:
            self._jsonld_buf.append(data)
        elif self._in_title:
            self.title += data
        elif not self._skip_depth:
            self.parts.append(data)


def _compact(value: str) -> str:
    value = re.sub(r"[ \t\r\f\v ]+", " ", value)
    value = re.sub(r" ?\n ?", "\n", value)
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def extract_text(html: str) -> str:
    parser = _Extractor()
    parser.feed(html)
    parser.close()
    out = [f"TITLE: {_compact(parser.title)}", _compact("".join(parser.parts))]
    blocks = []
    for raw in parser.jsonld:
        try:
            blocks.append(json.dumps(json.loads(raw), ensure_ascii=False))
        except ValueError:
            continue
    if blocks:
        out.append("JSON-LD:\n" + "\n".join(blocks))
    return "\n\n".join(p for p in out if p)[:MAX_TEXT_CHARS]
