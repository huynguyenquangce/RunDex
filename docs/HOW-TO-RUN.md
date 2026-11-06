# How to Run

Status: scaffold (step 1). Commands below work today; more are added as features land.

## Prerequisites
- Docker (for PostgreSQL and the API) or Python 3.12 for running the backend directly
- Node.js 22+ and npm
- Expo Go on a phone, or an Android emulator / iOS simulator

## Setup
```bash
cp src/.env.example src/.env     # dev-only defaults; change if you like
```

## Backend (API + database)
```bash
cd src
docker compose up --build        # PostgreSQL on :5432, API on :8000
curl http://localhost:8000/health   # {"status":"ok"}
```
Without Docker:
```bash
cd src/backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Docker Compose applies the migrations on start. The database starts **empty**: events come from the ingestion pipeline (see docs/INGESTION-PLAN.md), the product ships no seed data. Manual commands (with `DATABASE_URL` set, run in `src/backend`):
```bash
alembic upgrade head          # create/upgrade the schema
python -m app.seed tests/fixtures/events.fixture.yaml   # optional: load unverified TEST fixture data to look at screens locally
```

## API (step 3)
```bash
curl "http://localhost:8000/v1/events?q=da%20lat&type=trail&limit=10"
curl "http://localhost:8000/v1/events?distance=42&distance=ultra&region=south&open_only=true"
curl "http://localhost:8000/v1/events/vietnam-trail-marathon-2027"
```
Interactive docs: http://localhost:8000/docs. Parameters of `GET /v1/events`: `q` (every word must match; diacritics and case ignored), `type` (road|trail|mixed), `distance` (repeatable: 5, 10, 21, 42, ultra = 50 km and above), `region` (north|central|highlands|south), `from`/`to` (dates), `open_only`, `include_past`, `limit` (1-50, default 20), `cursor` (from `next_cursor`). The response has `items`, `next_cursor`, `total` (matches for the filters, used for "Show N events") and `last_updated_at`. The contract is committed in `src/openapi/openapi.json` (regenerate with `python -m app.export_openapi` in `src/backend`; CI fails if it is stale).

## Mobile app
```bash
cd src/mobile
npm install
npm start                        # Expo dev server; open in Expo Go or press a / i
```
API address: set `EXPO_PUBLIC_API_URL` (Android emulator reaches the host at `http://10.0.2.2:8000`).

## See the app on a phone (iPhone or Android, Windows or macOS laptop)
This is the development flow (no native build): the laptop runs the backend, the database and the Expo dev server (Metro); the phone runs **Expo Go** on the same network.

1. Install **Expo Go** (App Store / Google Play). Its SDK version must match the project (Expo SDK 58).
2. Laptop: start the backend with `docker compose up` in `src`, and find the laptop's LAN IP (`ipconfig` on Windows, IPv4 of the Wi-Fi adapter).
3. Laptop, in `src/mobile` (PowerShell example):
   ```powershell
   npm install
   $env:EXPO_PUBLIC_API_URL="http://<LAN IP>:8000"
   npx expo start
   ```
4. Phone on the same Wi-Fi: scan the QR code (iPhone: Camera app; Android: inside Expo Go). Allow ports 8081 (Metro) and 8000 (API) in the laptop firewall when asked.

Notes
- On the phone, `localhost` is the phone itself, so `EXPO_PUBLIC_API_URL` must be the laptop's IP.
- iOS cannot be simulated on Windows; use a real iPhone with Expo Go. An installable build (APK/IPA through EAS) is out of scope for now.
- Some company Wi-Fi networks block devices from reaching each other. If the QR code does not connect, use a phone hotspot or a home network. `npx expo start --tunnel` helps Metro only; the API must still be reachable.

## Test and check
Backend tests truncate tables, so they only run against a database named `*_test` (otherwise they are skipped with a message). Create one next to the dev database and point `DATABASE_URL` at it:
```bash
docker compose exec db createdb -U rundex rundex_test
DATABASE_URL=postgresql+psycopg://rundex:rundex_dev@localhost:5432/rundex_test REQUIRE_DB=1 pytest
```
```bash
cd src/backend && pytest && ruff check . && ruff format --check .   # DB tests need a database whose name ends in _test
cd src/mobile && npm run typecheck && npm test
cd src/mobile && npm run api:types    # regenerate src/api/schema.d.ts from src/openapi/openapi.json
```
`api:types` runs `openapi-typescript` through `npx` with its own TypeScript 5, because Expo SDK 58 uses TypeScript 6 and `openapi-typescript` does not support it yet (so it is not a project dependency).
CI runs the same checks on GitHub Actions (.github/workflows).

## Troubleshooting
- `docker: permission denied` on Linux/WSL: add your user to the `docker` group or use Docker Desktop with WSL integration.
- `npm install` is slow on a Windows drive from WSL: clone/work inside the WSL filesystem instead.
