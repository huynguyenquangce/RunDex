"""Build docs/ui-preview/index.html: an interactive HTML replica of the app screens.

It reads the catalog snapshot (no database needed), computes each event's detail with the same
backend code the API uses, and embeds the result in scripts/ui-preview.template.html.

    python scripts/build_ui_preview.py [--today YYYY-MM-DD] [--snapshot FILE] [--out FILE]

The output is deterministic: "today" defaults to the snapshot's export date, so the file only
changes when the snapshot, the backend status logic or the template change.
"""

import argparse
import json
import re
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "backend"))

from app.core.regions import REGIONS  # noqa: E402
from app.models import Distance, Event  # noqa: E402
from app.seed import EventSeed, load_seed_file  # noqa: E402
from app.services.events import to_detail  # noqa: E402

SNAPSHOT = ROOT / "src" / "backend" / "catalog" / "events.snapshot.yaml"
TEMPLATE = ROOT / "scripts" / "ui-preview.template.html"
OUT = ROOT / "docs" / "ui-preview" / "index.html"


def snapshot_date(path: Path) -> date | None:
    head = path.read_text(encoding="utf-8")[:400]
    match = re.search(r"exported (\d{4}-\d{2}-\d{2})", head)
    return date.fromisoformat(match.group(1)) if match else None


def to_event(seed: EventSeed) -> Event:
    event = Event(
        slug=seed.slug,
        name=seed.name,
        organizer=seed.organizer,
        event_type=seed.event_type,
        start_date=seed.start_date,
        end_date=seed.end_date,
        province=seed.province,
        venue=seed.venue,
        map_url=str(seed.map_url) if seed.map_url else None,
        description=seed.description,
        status=seed.status,
        registration_url=str(seed.registration_url) if seed.registration_url else None,
        registration_deadline=seed.registration_deadline,
        source_name=seed.source_name,
        source_url=str(seed.source_url) if seed.source_url else None,
        last_verified_at=seed.last_verified_at,
    )
    event.distances = [
        Distance(
            label=d.label,
            distance_km=Decimal(str(d.distance_km)),
            start_time=d.start_time,
            fee_vnd=d.fee_vnd,
            elevation_gain_m=d.elevation_gain_m,
            cutoff_minutes=d.cutoff_minutes,
            registration_deadline=d.registration_deadline,
        )
        for d in sorted(seed.distances, key=lambda x: -x.distance_km)
    ]
    return event


def build_html(
    snapshot: Path = SNAPSHOT, today: date | None = None, template: Path = TEMPLATE
) -> str:
    today = today or snapshot_date(snapshot) or date.today()
    seeds = sorted(load_seed_file(snapshot), key=lambda s: (s.start_date, s.slug))
    events = [to_detail(to_event(s), today).model_dump(mode="json") for s in seeds]
    data = {
        "generatedAt": today.isoformat(),
        "today": today.isoformat(),
        "regions": REGIONS,
        "events": events,
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return template.read_text(encoding="utf-8").replace("/*__DATA__*/", payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--today", type=date.fromisoformat)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    html = build_html(args.snapshot, args.today)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"wrote {args.out} ({len(html) // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
