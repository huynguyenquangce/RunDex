# Overview: RunDex

## Problem
Running events in Vietnam (road races, marathons, trail/ultra) are announced across Facebook pages, organizer sites and ticketing pages. There is no single, trustworthy, always-fresh view of upcoming events. Runners miss registration deadlines, struggle to compare distance/elevation/price/cut-off, and act on stale information (date changes, cancellations).

## What I am building
A **mobile app (iOS and Android)** with one purpose: **list all running events in Vietnam**. Opening an event shows its information clearly; a link to the organizer's official registration page is an add-on. The web client is designed later (ADR 0005). Data updates and new-event discovery are **automatic** through a scheduled ingestion pipeline with tiered trust (ADR 0002, 0003).

Name: **RunDex** (run + index: a catalog of running events). Availability on app stores, domains and trademarks not yet checked.

## Scope
- In (product): event list with basic search/sort/filter (date, region, type, distance; diacritic-insensitive search); event detail view (name, date/start time, location with map link, type, distances each with fee/elevation/cut-off/deadline, registration deadline, status, organizer, description, source and last-verified date); registration link (add-on, new tab).
- In (behind the scenes): source registry, scheduled fetch/refresh and discovery, AI extraction with confidence and evidence, deterministic validation, diff and change proposals, trust-tier decisions, review queue (minimal admin UI), audit log, link checker.
- Out: registration handling, end-user accounts, payments, reviews, virtual runs, activity tracking, notifications, web client (designed later).
- Assumption to confirm: basic filtering is included only to keep a long list usable.

## Users
- Runners looking for the next race (primary).
- Maintainer (me) reviewing risky changes and managing sources.

## Quality bar ("do it properly")
Scope is small, engineering is not: schema validation, tests, CI (lint/test/build, scheduled link check), one-command backend run (Docker Compose: PostgreSQL + API + worker), accessible mobile UI (dynamic text sizes, screen-reader labels, touch targets) with empty/loading/error states, offline-tolerant list (cached last data), deep link per event, ADR for every key decision, README with run steps.

## Architecture at a glance
Full diagrams and tech stack: `docs/ARCHITECTURE.md` (interactive page: https://claude.ai/artifact/SSqc3zJ4u7GyRyVsGm2YMU).

```
Mobile app (iOS + Android)  --REST/OpenAPI-->  API (FastAPI)  -->  PostgreSQL
                                                    ^
Source registry -> fetch -> raw store -> extract (rules / LLM) -> validate -> diff
   -> trust-tier decision -> auto-apply | review queue -> catalog
   worker/scheduler: refresh (by event proximity), discovery, link check; audit log on every change
```
Stack: PostgreSQL (ADR 0005, decided), FastAPI + worker/scheduler, Docker Compose for backend. Mobile framework: Expo (React Native + TypeScript), confirmed. LLM behind an adapter with a replay mode so reviewers can run without an API key. Reviewers run the app via Expo Go or an emulator; store publishing is not required.

## Design (Figma)
File: https://www.figma.com/design/ALbqe0EuRhmA2fW3BGlN7M (RunDex - Mobile App Design). Page "Mobile Screens": cover, color variables ("RunDex Colors"), and 3 screens per platform (Event List, Filters sheet, Event Detail) for iOS and Android, each with an Event Card component.
- Visual language: light neutral background, orange primary, soft status colors, rounded cards; iOS = large title + bottom sheet + pill chips, Android = top app bar + pill search + Material-style sheet.
- Fonts: iOS frames use Inter as a stand-in for SF Pro (SF Pro does not render in the design tool); Android uses Roboto. In code, use the system fonts.
- Data in frames is sample data, not verified. Status shown on each event: open, closing soon, not open yet, cancelled; source and last-verified date on the detail screen.
- Decision (owner, 2026-11-06): an alternative editorial/typographic direction was explored and discarded; keep this one.
- Not yet designed: empty-results and offline states, loading skeletons.
- Figma MCP call limit on the Starter plan was reached on 2026-11-06; the last restored version was not visually re-checked.

## Market check (2026-11-06, quick search, not exhaustive)
- No clearly dominant Vietnam-wide aggregator found. Existing options are mostly per-organizer apps (VnExpress Marathon, Sacombank Runners, UpRace, VietRace365) and listing pages (Endorphins Running, ITRA, blog lists). Gap hypothesis: neutral, always-fresh, all-event view with sources and last-verified dates. To be validated further.
- iRace (iRace.vn, has iOS/Android apps per its own site; app feature list not verified): mainly virtual runs with results synced from Strava/Garmin/Fitbit/Suunto, rule-based anti-fraud, paid tiers; also sells tickets for some real events. Positioning: closed platform, not a neutral multi-organizer calendar. Decision: real-world events only; organizers and ticketing platforms are data sources and registration links, not competitors to beat.
- Lesson borrowed from iRace: deterministic, transparent rules (not AI judgment) decide correctness; show exact deadlines and conditions.
- Search was limited (one pass, US-only tool); Facebook communities were not searchable.

## Risks and open items
- Source terms: robots.txt checked for some candidates, Terms of Service not yet reviewed; see `docs/DATA-SOURCES.md`. Must be done before enabling a source.
- No source is complete: "all events" is reached incrementally via the registry; MVP targets 3–5 sources and ~40–60 events.
- Wrong dates/cancellations harm users: tiered trust, review queue, visible source and last-verified date.
- LLM cost/variance: raw-doc caching, replay mode, call limits.
- Time: ~12 hours; cut-line below.
- Design tooling limit: Figma Starter plan MCP call limit reached; further design edits need a plan upgrade, a wait, or manual editing in Figma.
- Mobile adds testing/run friction: document Expo Go/emulator steps clearly; store publishing is out of scope.

Repository: https://github.com/huynguyenquangce/RunDex. See `docs/IMPLEMENTATION-PLAN.md` for the detailed plan of the existing screens (API, mobile, GitHub Actions, tests).

## Plan (4h/week, 13–30 Nov) and cut-line
| Week | Goal |
|---|---|
| 1 (13–19/11) | PostgreSQL schema + migrations, fixture data for tests only (events come from ingestion), API (list/detail/search with unaccent), mobile app skeleton with list and detail screens, tests, Docker Compose |
| 2 (20–26/11) | Ingestion core: source registry, fetch, one deterministic adapter + one AI adapter (with replay), validation, diff, change proposals, trust tiers, audit log |
| 3 (27–30/11) | Review queue (minimal admin), scheduler, link checker, CI, mobile UX/accessibility polish, docs/ADRs, reviewer-agent pass |

Cut-line if time runs short (drop in this order): review-queue UI polish → AI adapter live mode (keep replay) → link checker → second adapter. Never cut: data model, public UI, validation, tests, docs.

## Results / demo
_TBD_
