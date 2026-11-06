# How to Run RunDex

This guide takes you from a clean machine to the app running on your phone, step by step. Commands are for **Windows (PowerShell)**; macOS/Linux differences are noted. Each step ends with a **check** so you know it worked before moving on.

What runs where:

```
Your phone (Expo Go)  ──Wi-Fi──►  Expo dev server (Metro, :8081)   ┐
                      ──Wi-Fi──►  RunDex API (:8000)  ──► PostgreSQL (:5432)   ┘  all on your computer
```

Time needed: about 30 minutes the first time (downloads), 2 minutes afterwards.

---

## 0. What you need (one time)

| Tool | Why | Check |
|---|---|---|
| **Git** | get the code | `git --version` |
| **Node.js 22 or newer** (LTS) | the mobile app | `node -v` |
| **Docker Desktop** (running) | PostgreSQL + API | `docker version` shows a Client and a Server |
| **Expo Go** on your phone (App Store / Google Play) | open the app | installed |
| A phone and a computer on the **same Wi-Fi** | phone reaches the computer | see step 6 if the network blocks it |

macOS/Linux: install the same tools; use a normal terminal instead of PowerShell.

---

## 1. Get the code

```powershell
git clone https://github.com/huynguyenquangce/RunDex.git
cd RunDex
```
**Check:** `dir` (or `ls`) shows `src`, `docs`, `README.md`.

---

## 2. Start the backend (API + database)

```powershell
cd src
copy .env.example .env        # macOS/Linux: cp .env.example .env
docker compose up --build
```
The first run downloads images and takes a few minutes. Leave this window open: it is the server.

**Check 1:** the log ends with a line like `Uvicorn running on http://0.0.0.0:8000`.

**Check 2:** open <http://localhost:8000/health> in a browser. You should see `{"status":"ok"}`.
Also open <http://localhost:8000/docs> to browse the API.

---

## 3. Put data in the database

The database starts **empty**, and the app will say "Chưa có giải nào sắp diễn ra". Pick one option.

### Option A (2 minutes): load the unverified test fixture
Use this to see the screens quickly. Open a **second** terminal in `RunDex\src` (the API image does not contain the tests folder, so copy the file in first):
```powershell
docker compose cp backend/tests/fixtures/events.fixture.yaml api:/tmp/events.yaml
docker compose exec api python -m app.seed /tmp/events.yaml
```
**Check:** `seed: 10 created ...`, then <http://localhost:8000/v1/events> shows `"total": ...` with events. (The fixture events are 2026-2027 dates; events already in the past are hidden by default.)

### Option B (about 20 minutes): run the real ingestion pipeline
This downloads event pages from the registered sources and builds the catalog. It needs Python 3.12+ on your machine (or run it inside the API container, see below) and **Claude Code** for the extraction step.

1. Install the backend tools once (in `RunDex\src\backend`):
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
   pip install -e ".[dev]"
   $env:DATABASE_URL="postgresql+psycopg://rundex:rundex_dev@localhost:5432/rundex"   # macOS/Linux: export DATABASE_URL=...
   ```
2. Apply the database schema if the API container has not already done it, then run one pass:
   ```powershell
   alembic upgrade head
   python -m app.ingest run --limit 6
   ```
   This registers the sources and downloads pages into `src\backend\data\inbox` (polite: it respects `robots.txt` and waits between requests).
3. **Extraction (AI step).** Open Claude Code in the repository folder and ask it to run the extractor on the inbox, for example:
   > Run the event-extractor agent on the pages in src/backend/data/inbox.

   It writes one result file per page into `src\backend\data\outbox`. (If the named agent is not available in your session, ask Claude Code to follow `.claude/agents/event-extractor.md` itself.)
4. Apply the results and look at what is waiting:
   ```powershell
   python -m app.ingest apply
   python -m app.ingest review --summary
   ```
5. Decide. Events from official sources with high confidence are applied automatically; everything else waits for you:
   ```powershell
   python -m app.ingest review --limit 10                 # read the proposals and their evidence
   python -m app.ingest approve 12 15 20                  # approve by id
   python -m app.ingest approve --all --kind create --min-confidence 0.85   # many at once (look first)
   python -m app.ingest reject 14
   ```
   Approving stamps the event as checked today, so only approve what you have looked at.

**Check:** <http://localhost:8000/v1/events?limit=3> returns events and `total` is above 0.

Other ingestion commands: `fetch`, `apply`, `sources list`, `worker --interval-hours 24`. The `data` folder is git-ignored (downloaded page text is not committed).

---

## 4. Start the mobile app

Open a **new** terminal:
```powershell
cd RunDex\src\mobile
npm ci                          # first time only; takes a few minutes
```
Tell the app where the API is. The phone must use your **computer's Wi-Fi address**, not `localhost`.

Find the address:
- Windows: `ipconfig` → "Wireless LAN adapter Wi-Fi" → **IPv4 Address** (for example `192.168.1.20`)
- macOS: `ipconfig getifaddr en0`; Linux: `hostname -I`

Then start Expo (replace the address):
```powershell
$env:EXPO_PUBLIC_API_URL="http://192.168.1.20:8000"     # macOS/Linux: export EXPO_PUBLIC_API_URL=http://192.168.1.20:8000
npx expo start --clear
```
**Check:** the terminal shows a QR code and `Metro waiting on exp://192.168.1.20:8081`.

> The `$env:` variable only lives in this PowerShell window. Changing the address later? Stop Expo (Ctrl+C) and start again with `--clear`; the address is baked into the bundle.

---

## 5. Open it on your phone

1. Make sure the phone is on the **same Wi-Fi** as the computer.
2. **iPhone:** open the Camera app, point it at the QR code, tap the banner. **Android:** open Expo Go, tap "Scan QR code".
3. Wait for the bundle to download the first time (up to a minute).

**What you should see**
- **Danh sách:** the title "Giải chạy" (iPhone) or "RunDex" (Android), a search box, filter chips, and event cards showing date, type, status, place and distances.
- Type `da lat` in the search box: only Đà Lạt events remain (no need for accents).
- Tap chips such as **Trail** or **42K**; tap **Tất cả** to clear.
- Tap the **filter button** (next to the search box): choose type, distances, time range (this month / 3 / 6 months), region and "only open for registration". The green button shows how many events match ("Xem 12 giải"); tap it to apply, or **Xóa bộ lọc** to reset. The button on the list shows how many filter groups are active.
- Pull down to refresh. Scroll to the end to load more.
- Tap a card: **Chi tiết** with date and weekday, place and "Xem bản đồ", organizer, registration deadline, each distance with start time, fee, elevation and cut-off, the data source and when it was last checked.
- **Đăng ký trên trang ban tổ chức** opens the organizer's own page in the browser (only shown when the event has a link).
- Airplane mode after loading once, then reopen the app: the list is still there with a banner "Ngoại tuyến".

**Android emulator instead of a phone:** install Android Studio, start an emulator, press `a` in the Expo terminal. The emulator reaches the computer at `http://10.0.2.2:8000`, so you can skip `EXPO_PUBLIC_API_URL`.

**iOS simulator** exists only on macOS (press `i`). On Windows use a real iPhone with Expo Go.

---

## 6. If something does not work

| What you see | Likely cause | What to do |
|---|---|---|
| Phone cannot open the QR code / "could not connect" | Wi-Fi blocks devices from seeing each other (common on company or guest Wi-Fi), or the firewall blocks port 8081 | Use your phone's hotspot for the computer, or a home network. Allow ports 8081 and 8000 in the firewall (Windows admin PowerShell: `New-NetFirewallRule -DisplayName "RunDex dev" -Direction Inbound -Protocol TCP -LocalPort 8000,8081 -Action Allow -Profile Any`) |
| App says "Không tải được danh sách giải" | Wrong API address, API not running, or you forgot `--clear` after changing it | On the phone's browser open `http://<your IP>:8000/health`. If that fails it is the network/firewall. Then restart Expo with `--clear` |
| App says "Chưa có giải nào sắp diễn ra" | Database is empty | Step 3 |
| Expo Go says the project is incompatible | Expo Go older than the project's SDK 58 | Update Expo Go from the store |
| `npm ci` fails or is very slow | Network, or the folder is on a slow drive | Retry; on Windows keep the repo on a normal drive, not inside WSL's `/mnt/c`. If it complains about the lock file, delete `node_modules` and run `npm install` instead |
| `docker compose up` fails: port 5432 or 8000 in use | Another PostgreSQL/server on your machine | Stop it, or change the left-hand port numbers in `src/docker-compose.yml` |
| `docker: permission denied` (Linux) | Your user is not in the `docker` group | `sudo usermod -aG docker $USER`, then log out and in |
| On Linux/WSL the phone cannot reach the API | WSL2 does not expose ports to the LAN | Run Docker and Expo from Windows (Docker Desktop + PowerShell), or use mirrored networking |

---

## 7. Stop and clean up

- Expo: `Ctrl+C` in its terminal.
- Backend: `Ctrl+C`, then `docker compose down` in `src` (add `-v` to also delete the database data).

---

## 8. Run the tests and checks

Backend (in `src/backend`, with the virtual environment active):
```powershell
docker compose exec db createdb -U rundex rundex_test        # once; run from RunDex\src
$env:DATABASE_URL="postgresql+psycopg://rundex:rundex_dev@localhost:5432/rundex_test"; $env:REQUIRE_DB="1"
pytest
ruff check . ; ruff format --check .
```
The database tests **truncate tables**, so they refuse to run unless the database name ends in `_test`.

Mobile (in `src/mobile`):
```powershell
npm run typecheck
npm test
npm run api:types          # regenerate src/api/schema.d.ts from src/openapi/openapi.json
```
`api:types` runs `openapi-typescript` through `npx` with TypeScript 5 (Expo SDK 58 uses TypeScript 6, which it does not support yet).

Regenerate the API contract after changing the API (in `src/backend`): `python -m app.export_openapi`. CI fails when `src/openapi/openapi.json` or the generated types are out of date.

GitHub Actions runs the same checks on every push (`.github/workflows`).

---

## 9. Where things are

| Path | What |
|---|---|
| `src/backend` | FastAPI API, migrations, ingestion pipeline (`app/ingest`), tests |
| `src/mobile` | Expo app (screens in `src/app`, components in `src/components`) |
| `src/docker-compose.yml` | PostgreSQL + API for development |
| `docs/` | overview, architecture, ADRs, plans |
| `docs/INGESTION-PLAN.md` | how the data pipeline works |
