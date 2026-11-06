# ADR 0004: Event / Distance data model with provenance

- Status: accepted
- Date: 2026-11-06

## Context
One event has several distances, each with its own start time, fee, elevation gain, cut-off and registration deadline. Users must be able to trust each value, and the pipeline must explain every change.

## Decision
Core entities:
- **Event**: id, slug, name, organizer, type (road | trail | mixed), start_date, end_date, province, venue, map_url, description, status (scheduled | registration_open | registration_closed | postponed | cancelled | completed), registration_url, last_verified_at.
- **Distance** (belongs to Event): label, distance_km, start_time, fee_vnd, elevation_gain_m, cutoff_minutes, registration_deadline.
- **Source**: registry entry (url, kind, trust tier, frequency).
- **RawDocument**: fetched content, source, fetched_at.
- **ChangeProposal**: event, field, old, new, confidence, evidence, source, status (auto_applied | pending | approved | rejected), decided_by, decided_at.
- **AuditLog**: immutable record of applied changes.

Every public value can be traced to a source and time; the detail page shows source and last-verified date. Search is diacritic-insensitive (store a normalized name).

## Amendments (2026-11-06, step 2 implementation)
- `Event` also carries `registration_deadline` (event-level, shown on the detail screen); per-distance deadlines stay on `Distance`.
- `Event.search_text` is a generated column `lower(f_unaccent(name || province || venue || organizer))` with a trigram GIN index; `f_unaccent` is an IMMUTABLE wrapper around `unaccent` so it can back a generated column.
- Enumerations are `VARCHAR` plus CHECK constraints (not PostgreSQL enums) to keep migrations simple.
- `registration_url` is nullable: the app hides the registration action when it is missing.
- `distance_km` is `NUMERIC(6,2)` (marathon = 42.2, half = 21.1); the label ("42K") is what users see.
- Ingestion tables (`Source`, `RawDocument`, `ChangeProposal`, `AuditLog`) are not created yet.

## Alternatives considered
- Single flat event row: cannot represent per-distance data.
- Event-sourcing everything: heavier than needed; ChangeProposal + AuditLog give enough history.

## Consequences
- More tables, but clear provenance and review flow.
- Migrations needed as fields evolve (PostgreSQL from day one, ADR 0005).

## AI involvement
AI proposed the model; the owner confirmed the detail-page fields. Field list can still change after review.
