# ADR 0005: PostgreSQL from day one; mobile-first (iOS + Android), web later

- Status: accepted
- Date: 2026-11-06

## Context
The owner wants the product to be a mobile app for iOS and Android first; the web client is designed later. The owner also wants PostgreSQL directly instead of starting on SQLite.

## Decision
- **Database:** PostgreSQL, run through Docker Compose. No SQLite stage.
- **Platform:** mobile app (iOS + Android) is the primary client. A versioned REST API (with OpenAPI) is the contract, so a web client can be added later without backend changes.
- **Mobile framework (confirmed by owner 2026-11-06):** Expo (React Native + TypeScript), one codebase for both platforms.
- **Backend:** FastAPI + worker/scheduler for the ingestion pipeline (ADR 0003), same Compose stack as PostgreSQL.

## Alternatives considered
- SQLite first: simpler, but the owner prefers no later migration; Postgres also fits scheduled jobs and full-text/unaccent search.
- Flutter: strong UI and performance, Dart is less common; Expo chosen as proposal for TypeScript sharing with a future web client and easy review via Expo Go.
- Native Swift + Kotlin: two codebases, too costly for ~12 hours.
- Web-first or PWA: contradicts the owner's priority.

## Consequences
- SEO/per-URL pages are no longer a day-one goal; deep links per event replace them. Revisit with the web client.
- Store publishing is not required for the challenge: reviewers run the backend with Docker Compose and the app via Expo Go or an emulator (documented in HOW-TO-RUN).
- Mobile concerns enter the design: offline-tolerant list (cache last data), loading/empty/error states, accessibility (dynamic type, screen-reader labels, touch targets), pagination.
- Search uses PostgreSQL `unaccent` for diacritic-insensitive Vietnamese search.
- Push notifications stay out of scope.

## AI involvement
AI proposed framework options and trade-offs; the owner decided PostgreSQL and mobile-first. Owner confirmed Expo.
