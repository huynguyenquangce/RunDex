"""The HTML UI preview (docs/ui-preview) must keep behaving like the API it imitates."""

import calendar
import importlib.util
import json
import shutil
import subprocess
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.deps import get_today
from app.main import app
from app.seed import load_seed_file, seed_events

ROOT = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location(
    "build_ui_preview", ROOT / "scripts" / "build_ui_preview.py"
)
assert _spec and _spec.loader
preview = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(preview)

SNAPSHOT_DAY = preview.snapshot_date(preview.SNAPSHOT) or date(2026, 11, 6)


def _end_of_month(d: date) -> date:
    return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


def _add_months(d: date, n: int) -> date:
    y, m = d.year + (d.month - 1 + n) // 12, (d.month - 1 + n) % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _cases(today: date) -> list[dict]:
    month = {"from": str(today), "to": str(_end_of_month(today))}
    next3 = {"from": str(today), "to": str(_add_months(today, 3))}
    return [
        {},
        {"type": "trail"},
        {"type": "road"},
        {"q": "da lat"},
        {"q": "ĐÀ LẠT"},
        {"q": "heritage marathon"},
        {"q": "xyz"},
        {"distance": ["42"]},
        {"distance": ["ultra"]},
        {"distance": ["21", "42"]},
        {"region": "south"},
        {"region": "north"},
        {"region": "central"},
        {"region": "highlands"},
        {"openOnly": True},
        month,
        next3,
        {"type": "trail", "region": "highlands"},
        {"type": "road", "distance": ["42"], "openOnly": True},
        {"q": "trail", **next3},
    ]


def _api_params(f: dict) -> dict:
    params: dict = {"limit": 1}
    for key, name in (
        ("q", "q"),
        ("type", "type"),
        ("distance", "distance"),
        ("region", "region"),
        ("from", "from"),
        ("to", "to"),
    ):
        if f.get(key):
            params[name] = f[key]
    if f.get("openOnly"):
        params["open_only"] = "true"
    return params


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    seed_events(db, load_seed_file(preview.SNAPSHOT))
    app.dependency_overrides[get_today] = lambda: SNAPSHOT_DAY
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_preview_filters_give_the_same_counts_as_the_api(
    client: TestClient, tmp_path: Path
) -> None:
    html = tmp_path / "index.html"
    html.write_text(preview.build_html(today=SNAPSHOT_DAY), encoding="utf-8")
    cases = _cases(SNAPSHOT_DAY)
    (tmp_path / "cases.json").write_text(json.dumps(cases), encoding="utf-8")
    checker = ROOT / "scripts" / "ui-preview-crosscheck.js"
    out = subprocess.run(
        ["node", str(checker), str(html), str(tmp_path / "cases.json")],
        capture_output=True,
        text=True,
        check=True,
    )
    js_counts = json.loads(out.stdout)
    api_counts = [client.get("/v1/events", params=_api_params(f)).json()["total"] for f in cases]
    assert js_counts == api_counts, list(zip(cases, js_counts, api_counts, strict=True))


def test_build_is_deterministic_and_lists_every_snapshot_event() -> None:
    first = preview.build_html(today=SNAPSHOT_DAY)
    assert first == preview.build_html(today=SNAPSHOT_DAY)
    for seed in load_seed_file(preview.SNAPSHOT):
        assert f'"slug":"{seed.slug}"' in first


def test_event_text_cannot_break_out_of_the_data_script(tmp_path: Path) -> None:
    snapshot = tmp_path / "events.snapshot.yaml"
    snapshot.write_text(
        "# exported 2026-11-06\nevents:\n"
        "- slug: evil-2027\n  name: 'A </script><script>alert(1)</script>'\n"
        "  event_type: road\n  start_date: '2027-01-01'\n",
        encoding="utf-8",
    )
    html = preview.build_html(snapshot, today=date(2026, 11, 6))
    data_block = html.split('<script id="data" type="application/json">')[1].split("</script>")[0]
    assert "</script>" not in data_block and "<script>" not in data_block
    assert "\\u003c/script>" in data_block


def test_committed_preview_file_is_a_valid_page() -> None:
    page = (ROOT / "docs" / "ui-preview" / "index.html").read_text(encoding="utf-8")
    assert page.startswith("<!doctype html>") and 'id="data"' in page and "/*__DATA__*/" not in page
