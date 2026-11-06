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

Docker Compose applies migrations and loads the sample data on start (idempotent). Manual commands (with `DATABASE_URL` set, run in `src/backend`):
```bash
alembic upgrade head          # create/upgrade the schema
python -m app.seed            # load seed/events.sample.yaml (SAMPLE, unverified data)
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

## Test and check
```bash
cd src/backend && pytest && ruff check . && ruff format --check .
cd src/mobile && npm run typecheck && npm test
cd src/mobile && npm run api:types    # regenerate src/api/schema.d.ts from src/openapi/openapi.json
```
`api:types` runs `openapi-typescript` through `npx` with its own TypeScript 5, because Expo SDK 58 uses TypeScript 6 and `openapi-typescript` does not support it yet (so it is not a project dependency).
CI runs the same checks on GitHub Actions (.github/workflows).

## Troubleshooting
- `docker: permission denied` on Linux/WSL: add your user to the `docker` group or use Docker Desktop with WSL integration.
- `npm install` is slow on a Windows drive from WSL: clone/work inside the WSL filesystem instead.
