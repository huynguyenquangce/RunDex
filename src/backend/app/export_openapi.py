"""Write the OpenAPI contract to src/openapi/openapi.json (checked in CI for drift)."""

import json
import sys
from pathlib import Path

from app.main import app

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "openapi" / "openapi.json"


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(app.openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
