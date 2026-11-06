# How to Run RunDex (WSL / Linux)

Step by step, from a clean WSL (Ubuntu) to the app on your phone. **Every command runs in the WSL terminal** unless a step says "Windows PowerShell (admin)". Each step ends with a **Check** so you know it worked before moving on.

What runs where:

```
Phone (Expo Go) ──Wi-Fi──► Expo dev server (Metro :8081)            ┐
                ──Wi-Fi──► RunDex API (:8000) ──► PostgreSQL (:5432) ┘  all inside WSL
```

Time: about 30 minutes the first time (downloads), 2 minutes afterwards.

---

## 0. Prerequisites (one time)

In WSL:
```bash
sudo apt update
sudo apt install -y git curl python3-venv python3-pip
node -v        # must be v22 or newer; if not: curl -fsSL https://fnm.vercel.app/install | bash   (then: fnm install 22)
docker version # must show a Client and a Server
```
- **Docker:** either Docker Desktop (Windows) with "WSL integration" enabled for your distro, or Docker Engine installed inside WSL. If `docker version` says *permission denied*:
  ```bash
  sudo usermod -aG docker $USER
  # close the WSL terminal, run `wsl --shutdown` in Windows PowerShell, then open WSL again
  ```
- **Expo Go** on your phone (App Store / Google Play).
- Phone and computer on the **same Wi-Fi** (step 7 covers networks that block it).

---

## 1. Get the code (inside the WSL filesystem)

Keep the project in your WSL home, **not** under `/mnt/c/...` (the Windows drive is very slow for `npm`).
```bash
cd ~
git clone https://github.com/huynguyenquangce/RunDex.git
cd RunDex
```
**Check:** `ls` shows `src`, `docs`, `README.md`.

---

## 2. Start the backend (API + database)

```bash
cd ~/RunDex/src
cp .env.example .env
docker compose up --build
```
The first run downloads images (a few minutes). Leave this terminal open: it is the server.

**Check 1:** the log ends with `Uvicorn running on http://0.0.0.0:8000`.

**Check 2** (second WSL terminal):
```bash
curl http://localhost:8000/health        # {"status":"ok"}
```
You can also open <http://localhost:8000/docs> in the Windows browser.

---

## 3. Put data in the database

The database starts **empty** and the app will say "Chưa có giải nào sắp diễn ra". Pick one option.

### Option A (2 minutes): load the unverified test fixture
In the second terminal:
```bash
cd ~/RunDex/src
docker compose cp backend/tests/fixtures/events.fixture.yaml api:/tmp/events.yaml
docker compose exec api python -m app.seed /tmp/events.yaml
```
**Check:** `seed: 10 created ...`, then `curl "http://localhost:8000/v1/events?limit=3"` returns events. (The fixture dates are 2026 to 2027; events already in the past are hidden by default.)

### Option B (about 20 minutes): run the real ingestion pipeline
Downloads event pages from the registered sources and builds the catalog. The AI extraction step uses **Claude Code**.

1. Set up the backend tools once:
   ```bash
   cd ~/RunDex/src/backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   export DATABASE_URL="postgresql+psycopg://rundex:rundex_dev@localhost:5432/rundex"
   ```
2. Apply the schema if the API container has not, then one pass:
   ```bash
   alembic upgrade head
   python -m app.ingest run --limit 6
   ```
   It registers the sources and downloads pages into `src/backend/data/inbox` (polite: it respects `robots.txt` and waits between requests).
3. **Extraction (AI step).** Open Claude Code in `~/RunDex` and ask:
   > Run the event-extractor agent on the pages in src/backend/data/inbox.

   It writes one result file per page into `src/backend/data/outbox`. (If the named agent is not available in that session, ask Claude Code to follow `.claude/agents/event-extractor.md` itself.)
4. Apply the results and see what waits:
   ```bash
   python -m app.ingest apply
   python -m app.ingest review --summary
   ```
5. Decide. High-confidence events from official sources are applied automatically; everything else waits for you:
   ```bash
   python -m app.ingest review --limit 10                  # read proposals and their evidence
   python -m app.ingest approve 12 15 20                   # approve by id
   python -m app.ingest approve --all --kind create --min-confidence 0.85   # many at once (look first)
   python -m app.ingest reject 14
   ```
   Approving stamps the event as checked today, so approve only what you have looked at.

**Check:** `curl "http://localhost:8000/v1/events?limit=3"` returns events and `"total"` is above 0.

Other commands: `fetch`, `apply`, `sources list`, `worker --interval-hours 24`. The `data/` folder is git-ignored.

---

## 4. Let the phone reach WSL (important)

WSL2 has its own virtual network, so by default **only Windows** can see its ports, not your phone. Choose one fix (A is simpler). These are the only Windows-side commands in this guide.

### Fix A: mirrored networking (Windows 11 22H2 or newer)
1. In WSL, create or edit the WSL settings file (it lives in your Windows user folder; replace `<WindowsUser>`):
   ```bash
   nano /mnt/c/Users/<WindowsUser>/.wslconfig
   ```
   Put this in it and save:
   ```
   [wsl2]
   networkingMode=mirrored
   ```
2. Windows PowerShell **as Administrator**: allow connections from the LAN into WSL, then restart WSL:
   ```powershell
   Set-NetFirewallHyperVVMSetting -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -DefaultInboundAction Allow
   wsl --shutdown
   ```
3. Open WSL again and start the backend again (step 2).

WSL now shares the Windows network address. **Check (in WSL):** `hostname -I` shows your Wi-Fi address (for example `192.168.1.20`). Call it `<address>`: it is what the phone uses.

### Fix B: forward the ports (any Windows 10/11)
1. In WSL, get WSL's own address: `hostname -I | awk '{print $1}'` (example `172.28.112.5`).
2. Find your Windows **Wi-Fi IPv4 address**. From WSL you can ask Windows:
   ```bash
   powershell.exe -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Wi-Fi').IPAddress"
   ```
   (example `192.168.1.20`; this is `<address>`).
3. Windows PowerShell **as Administrator** (replace both addresses):
   ```powershell
   netsh interface portproxy add v4tov4 listenaddress=192.168.1.20 listenport=8000 connectaddress=172.28.112.5 connectport=8000
   netsh interface portproxy add v4tov4 listenaddress=192.168.1.20 listenport=8081 connectaddress=172.28.112.5 connectport=8081
   New-NetFirewallRule -DisplayName "RunDex dev" -Direction Inbound -Protocol TCP -LocalPort 8000,8081 -Action Allow -Profile Any
   ```
4. WSL's address changes after every WSL restart: redo step 1 and the two `netsh` lines when it does (remove old ones with `netsh interface portproxy delete v4tov4 listenaddress=192.168.1.20 listenport=8000`).

### Check it before opening the app
On the **phone's browser** open `http://<address>:8000/health`. You must see `{"status":"ok"}`. If not, fix the network first (step 7), not the app.

---

## 5. Start the mobile app

New WSL terminal. `<address>` is the Wi-Fi address from step 4.
```bash
cd ~/RunDex/src/mobile
npm ci                                   # first time only; a few minutes
export EXPO_PUBLIC_API_URL="http://<address>:8000"
export REACT_NATIVE_PACKAGER_HOSTNAME="<address>"     # Expo advertises the address the phone can reach
npx expo start --clear
```
**Check:** the terminal shows a QR code and `exp://<address>:8081`.

> The two `export` lines only last for this terminal. If the address changes, stop Expo (Ctrl+C), export again and start with `--clear` (the API address is baked into the bundle).

---

## 6. Open it on the phone

1. Phone on the **same Wi-Fi** as the computer.
2. **iPhone:** Camera app, point at the QR code, tap the banner. **Android:** Expo Go, "Scan QR code".
3. Wait for the first bundle download (up to a minute).

**What you should see**
- **Danh sách:** title "Giải chạy" (iPhone) or "RunDex" (Android), search box, filter button, chips, event cards (date, type, status, place, distances).
- Type `da lat` in the search box: only Đà Lạt events remain (accents are not needed).
- Chips such as **Trail** or **42K** filter; **Tất cả** clears.
- **Filter button:** type, distances, time range (this month / 3 / 6 months), region, "only open for registration". The green button shows how many events match ("Xem 12 giải"); **Xóa bộ lọc** resets; a badge on the list's filter button shows how many groups are active.
- Pull down to refresh; scroll to the end to load more.
- Tap a card: **Chi tiết** with weekday and date, place and "Xem bản đồ", organizer, registration deadline, each distance (start time, fee, elevation, cut-off), the data source and when it was last checked.
- **Đăng ký trên trang ban tổ chức** opens the organizer's own page in the browser (only when the event has a link).
- Airplane mode after loading once, reopen the app: the list is still there with a banner "Ngoại tuyến".

Emulators are not covered here (iOS simulators need macOS, Android Studio runs on the Windows side). Use a real phone with Expo Go.

---

## 7. If something does not work

| What you see | Likely cause | What to do |
|---|---|---|
| Windows browser opens `localhost:8000` but the phone cannot open `http://<address>:8000/health` | WSL2's network is not exposed to the LAN | Step 4 (mirrored networking or port forwarding) |
| `ERR_CONNECTION_REFUSED` on `<address>:8000` from Windows itself | Nothing listening: backend not running, or the port forward points to an old WSL address | Start the backend; for Fix B redo the `netsh` lines with the current `hostname -I` |
| Phone times out (spinner) but the backend works in Windows | Firewall, or the Wi-Fi isolates devices (common on company or guest Wi-Fi) | Add the firewall rule from step 4; otherwise use your phone's hotspot for the computer and repeat step 4 with the new address (iPhone hotspots use `172.20.10.x`) |
| QR code opens Expo Go but "could not connect" / "unable to load" | Expo advertises WSL's internal address | Set `REACT_NATIVE_PACKAGER_HOSTNAME` (step 5) and restart with `--clear` |
| App says "Không tải được danh sách giải" | Wrong API address, API not running, or you forgot `--clear` after changing it | Test `http://<address>:8000/health` on the phone, then restart Expo with `--clear` |
| App says "Chưa có giải nào sắp diễn ra" | Database is empty | Step 3 |
| Expo Go says the project is incompatible | Expo Go older than SDK 58 | Update Expo Go from the store |
| `npm ci` is very slow | Repo is under `/mnt/c` | Clone into `~` (step 1) |
| `npm ci` complains about the lock file | Platform differences | `rm -rf node_modules && npm install` |
| `docker: permission denied` | Your user is not in the `docker` group | Step 0 |
| `docker compose up`: port 5432 or 8000 already in use | Another PostgreSQL/server on the machine | Stop it, or change the left-hand port numbers in `src/docker-compose.yml` |
| `curl localhost:8000` hangs inside WSL | Containers stopped | `docker compose ps` in `~/RunDex/src` |

---

## 8. Stop and clean up

- Expo: `Ctrl+C` in its terminal.
- Backend: `Ctrl+C`, then `docker compose down` in `~/RunDex/src` (add `-v` to also delete the database data).
- Fix B only: remove the forwards with `netsh interface portproxy reset` (Windows PowerShell as Administrator).

---

## 9. Run the tests and checks

Backend (in `~/RunDex/src/backend`, virtual environment active):
```bash
docker compose -f ../docker-compose.yml exec db createdb -U rundex rundex_test    # once
export DATABASE_URL="postgresql+psycopg://rundex:rundex_dev@localhost:5432/rundex_test" REQUIRE_DB=1
pytest
ruff check . && ruff format --check .
```
The database tests **truncate tables**, so they refuse to run unless the database name ends in `_test`.

Mobile (in `~/RunDex/src/mobile`):
```bash
npm run typecheck
npm test
npm run api:types      # regenerate src/api/schema.d.ts from src/openapi/openapi.json
```
`api:types` runs `openapi-typescript` through `npx` with TypeScript 5 (Expo SDK 58 uses TypeScript 6, which it does not support yet).

After changing the API, regenerate the contract (in `src/backend`): `python -m app.export_openapi`. CI fails when `src/openapi/openapi.json` or the generated types are out of date. GitHub Actions runs the same checks on every push.

---

## 10. Where things are

| Path | What |
|---|---|
| `src/backend` | FastAPI API, migrations, ingestion pipeline (`app/ingest`), tests |
| `src/mobile` | Expo app (screens in `src/app`, components in `src/components`) |
| `src/docker-compose.yml` | PostgreSQL + API for development |
| `docs/` | overview, architecture, ADRs, plans |
| `docs/INGESTION-PLAN.md` | how the data pipeline works |
