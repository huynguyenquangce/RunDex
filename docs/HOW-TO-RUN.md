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
cd src/mobile && npm run typecheck
```
CI runs the same checks on GitHub Actions (.github/workflows).

## Troubleshooting
- `docker: permission denied` on Linux/WSL: add your user to the `docker` group or use Docker Desktop with WSL integration.
- `npm install` is slow on a Windows drive from WSL: clone/work inside the WSL filesystem instead.
