# ADR 0002: Product scope (event list + detail view; organizer link as add-on; automated data upkeep)

- Status: accepted (revised 2026-11-06, replaces first version that excluded AI from the product)
- Date: 2026-11-06

## Context
The owner wants one goal: list all running events in Vietnam. Clicking an event shows its information clearly; a link to the organizer's registration page is an add-on. Data must update automatically, and new events must be discovered automatically. iRace-style platforms already cover virtual runs, results sync and ticketing, so we do not compete there.

## Decision
- Product surface: event list, event detail view, outbound registration link (add-on). Nothing else: no registration handling, accounts for end users, payments, reviews, tracking or virtual runs.
- Behind the surface: an automated ingestion pipeline (ADR 0003) keeps data fresh and discovers new events. AI is used inside the pipeline for extraction only, never as the judge of correctness.

## Alternatives considered
- Static site with hand-edited data files: simple, but not automatic; rejected after the owner required automatic updates.
- Full platform (accounts, reminders, reviews): exceeds ~12 hours and competes with organizer platforms.

## Consequences
- Value comes from completeness, freshness and correctness of data; most design effort goes to ingestion, trust and review.
- Needs backend, database, scheduler and a small admin/review UI.
- "All events" is approached incrementally through a registry of sources, not promised on day one.

## AI involvement
AI proposed richer scopes and the pipeline idea; the owner narrowed the product surface and required automation. AI is a build-time tool (code generation) and a runtime extractor inside the pipeline; its inputs are in ai-inputs/.
