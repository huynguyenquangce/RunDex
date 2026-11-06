# Implementation Plan: screens already designed (Event List, Filters, Event Detail)

Status: accepted by the owner, 2026-11-06 (see ADR 0006). Coding starts 2026-11-13 (challenge window). Figma work for additional screens is postponed. Items marked (confirm) are proposals awaiting the owner's decision.

Progress: step 1 (scaffold, CI skeleton) done and pushed on 2026-11-06. First CI run: backend and mobile green; Security (gitleaks) red, caused by placeholder DB passwords, handled with .gitleaks.toml (to be confirmed by the next run). Step 6 (Event Detail screen from the Figma design: badges, title, status notice for cancelled/postponed/completed, date with weekday and start time, place with map link, organizer, registration deadline card, distance cards with start time/fee/elevation/cut-off, source and last-verified line, bottom button to the organizer's page; links are checked to be http(s)) done 2026-11-06: 35 Jest tests, typecheck and bundles pass; not yet seen on a device. docs/HOW-TO-RUN.md rewritten step by step. Step 5 (Event List screen from the Figma design: iOS large title / Android app bar, debounced diacritic-insensitive search, quick filter chips, event cards, skeleton, empty, error and offline states, infinite scroll, pull to refresh; icons via react-native-svg) done 2026-11-06: typecheck, 21 Jest tests, expo-doctor and Android + iOS bundle exports pass; not yet seen on a device. The filter button and sheet come in step 7. Step 4 (Expo app wiring: router, TanStack Query with persisted cache, typed API client generated from OpenAPI, theme tokens, raw list and detail screens, Jest tests) done 2026-11-06: typecheck, 8 Jest tests, expo-doctor (20/20) and an Android bundle export pass locally; not yet run on a device or in CI. Step 3 (list/detail API, keyset pagination, filters, OpenAPI contract, tests) written 2026-11-06. Step 2 (schema, Alembic migration 0001, seed loader and 10 sample events, tests) written 2026-11-06: ruff and non-DB tests pass locally; database tests need PostgreSQL and run in GitHub Actions (REQUIRE_DB=1) because the dev machine has no Docker access yet.

## Goal
A working mobile app (iOS + Android, Expo) backed by a real API and PostgreSQL that shows the event list with search and filters, and an event detail screen with a link to the organizer's registration page. Verified by tests and GitHub Actions. Ingestion (ADR 0003) comes after.

## Repository layout (confirm)
Monorepo, the GitHub repo root is the submission folder.
```
.github/workflows/        ci-backend.yml, ci-mobile.yml, security.yml, build-preview.yml (manual)
.github/dependabot.yml
src/
  docker-compose.yml      db + api (+ later worker)
  backend/                FastAPI app
    app/ (api/, models/, schemas/, services/, core/)
    alembic/  tests/ (fixtures/events.fixture.yaml)  pyproject.toml  Dockerfile
  mobile/                 Expo app (TypeScript strict)
    app/ (expo-router: index, event/[slug])
    src/ (api/, components/, features/, theme/, i18n/)  __tests__/
  openapi/openapi.json    generated contract, committed
docs/  ai-inputs/  scripts/
```

## Backend design
- Stack: Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, Pydantic v2, PostgreSQL 16, ruff, pytest (confirm ORM choice).
- Schema (ADR 0004 subset for now): `events`, `distances`; ingestion tables later. Extensions: `unaccent`, `pg_trgm`. Normalized search column (unaccented, lowercased name + province).
- Endpoints (versioned `/v1`):
  - `GET /v1/events` query: `q`, `type` (road|trail), `distance_km` (multi), `region`, `from`, `to`, `open_only`, `limit` (default 20, max 50), `cursor`. Sorted by `start_date, id`; keyset pagination (cursor = last start_date + id). Response: items + `next_cursor` + `last_updated_at`.
  - `GET /v1/events/{slug}`: full event with distances, source, `last_verified_at`.
  - `GET /health`.
- Derived fields computed server-side: `closing_soon` (deadline within 7 days), `days_left`, `status`.
- Errors: consistent problem-style JSON; 404 for unknown slug; 422 for bad filters.
- No seed data in the product (owner decision 2026-11-06): events arrive through the ingestion pipeline (docs/INGESTION-PLAN.md). `tests/fixtures/events.fixture.yaml` holds 10 unverified events used only by tests; `python -m app.seed <file>` can load them locally.
- Config: env vars only (`DATABASE_URL`), `.env.example`, no secrets in repo.

## Mobile design
- Expo SDK (latest stable), Expo Router, TypeScript strict, ESLint + Prettier.
- Data: TanStack Query with persisted cache (AsyncStorage) so the list works offline with a "last saved" banner; infinite query on cursor.
- API client: types generated from `openapi.json` (openapi-typescript) so the contract cannot drift (confirm).
- Theme: tokens mirrored from Figma "RunDex Colors" (primary #FF5A1F, ink #111827, bg #F5F6F8, etc.) in `src/theme`; system fonts (iOS SF, Android Roboto) in the real app; Figma uses Inter as a stand-in for SF Pro.
- Screens (from Figma):
  1. Event List: large title (iOS) / top app bar (Android), search field (debounced, diacritic-insensitive on server), chip row, month-grouped or flat list of Event Cards, pull to refresh, infinite scroll.
  2. Filters sheet: type, distance, time, region, open-only; apply shows result count; clear.
  3. Event Detail: badges, title, date/location/organizer, registration deadline, distances list, source and last-verified, bottom CTA opens `registration_url` via `Linking` (add-on), deep link `rundex://event/{slug}`.
  4. States: loading skeleton, empty results, offline banner, error with retry (designed later in Figma, implemented with simple versions first).
- Accessibility: labels on all touchables, `allowFontScaling`, 44pt targets, contrast checked against tokens.
- Config: `EXPO_PUBLIC_API_URL` (Android emulator uses `http://10.0.2.2:8000`).

## GitHub Actions (CI/CD)
| Workflow | Trigger | Steps |
|---|---|---|
| `ci-backend.yml` | PR + push to main, paths `src/backend/**` | ruff, pytest with `postgres` service container, `alembic upgrade head` on empty DB, regenerate OpenAPI and fail on diff, build Docker image |
| `ci-mobile.yml` | PR + push, paths `src/mobile/**` | `npm ci`, `tsc --noEmit`, eslint, jest, `expo-doctor`, regenerate API types and fail on diff |
| `security.yml` | PR + weekly | gitleaks (secrets), dependency review, `pip-audit` / `npm audit` (report) |
| `build-preview.yml` | manual (`workflow_dispatch`) | EAS build preview for Android (and iOS if an Apple account exists); needs `EXPO_TOKEN` secret (optional, not required for the challenge) |
| `dependabot.yml` | weekly | npm, pip, github-actions |
Rules: no secrets in repo; least-privilege `permissions:`; pin actions to major versions or SHAs; caching for pip/npm. Store publishing is out of scope.
Note (confirm): GitHub hosting must be allowed for this work under KMS policy; do not push client or confidential data. The workflows are also included in the submission folder.

## Testing strategy
- Backend: pytest + httpx AsyncClient against a real PostgreSQL; cover filters, keyset pagination (stable, no duplicates), unaccent search (`da lat` finds Đà Lạt), detail 404, closing_soon logic, seed idempotency.
- Mobile: Jest + React Native Testing Library; cover list rendering, filter state to query params, debounced search, offline banner, CTA opens the URL (mock Linking). API mocked with MSW.
- Manual: run on Android emulator and iOS simulator, record screenshots for docs.

## Work breakdown (hours, assuming AI generates and I review)
| # | Task | Output | h |
|---|---|---|---|
| 1 | Scaffold repo, Compose, CI skeleton, `.env.example` | green CI on empty app | 0.75 |
| 2 | Schema + Alembic + fixture loader | migrations apply; tests load fixture events | 0.75 |
| 3 | List/detail API + search + tests | OpenAPI contract committed | 1.25 |
| 4 | Mobile scaffold, theme, API client, query cache | app boots and calls API | 0.75 |
| 5 | Event List screen (search, chips, cards, infinite scroll) | matches Figma | 1.0 |
| 6 | Event Detail screen + CTA + deep link | matches Figma | 0.75 |
| 7 | Filters sheet | filters change list | 0.75 |
| 8 | States (loading, empty, offline, error) + a11y pass | resilient UX | 0.75 |
| 9 | Docs, ADRs, HOW-TO-RUN, prompt log, reviewer agent pass | submission-ready | 0.5 |
Total about 7.25 h, roughly week 1 plus half of week 2. This leaves about 4.5 h for ingestion (ADR 0003) and polish, which is tight.

## Milestones and definition of done
- M1 (end of week 1): tasks 1–4 done; API serves events from the database (fixtures in tests, ingestion in the product); app shows a raw list; CI green.
- M2 (early week 2): tasks 5–8 done; all three screens and states work on both platforms.
- M3: docs and ADRs updated, `scripts/check-submission.sh` passes, reviewer agent run.
Done = tests pass in CI, runs with documented commands from a clean clone, no secrets, docs match code.

## Cut-line if time runs short (drop in order)
build-preview workflow → pip/npm audit steps → persisted offline cache (keep banner with in-memory cache) → state polish → month grouping on the list. Never cut: schema, API tests, list + detail screens, CI for backend and mobile, docs.

## Risks
- ~7 h for the screens leaves little for ingestion: consider shipping ingestion as a thin vertical slice (one adapter + replay).
- Expo Go limits: bottom sheet and gestures must use libraries supported by Expo Go; fall back to a modal sheet if needed.
- Android emulator networking (`10.0.2.2`) and Docker on Windows/WSL: document in HOW-TO-RUN.
- Starting before 13/11 is not planned; coding starts at the beginning of the challenge window.

## Decisions (confirmed 2026-11-06)
1. Monorepo with `src/backend` and `src/mobile`: confirmed.
2. Libraries (SQLAlchemy + Alembic, TanStack Query, expo-router, openapi-typescript): accepted as fitting the current scope; may change with a new ADR.
3. Repository: https://github.com/huynguyenquangce/RunDex (owner's account; keep client and confidential data out).
4. EAS preview builds: skipped for now.
