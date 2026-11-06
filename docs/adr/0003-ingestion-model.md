# ADR 0003: Scheduled ingestion pipeline with tiered trust

- Status: accepted
- Date: 2026-11-06

## Context
Event data is scattered and changes (dates, fees, cancellations). Wrong registration or date data harms users. No single complete source exists; scraping social networks is fragile and violates terms. We need automatic refresh of known events and discovery of new ones, within ~12 hours of build time.

## Decision
A pull-based, scheduled pipeline:

1. **Source registry** (config): URL, kind (listing / event page / feed), refresh frequency, trust tier, allowed-use notes. Adding a source is configuration, not code.
2. **Fetch** via per-source adapters; store raw documents with fetch time (replayable).
3. **Extract**: structured pages parsed deterministically; free-form pages via LLM into the event schema, each field with confidence and a quoted evidence snippet.
4. **Validate** with deterministic rules (valid dates, numeric distances, link domain matches organizer, no duplicates).
5. **Diff** against the stored event; produce change proposals (field, old, new, confidence, evidence, source).
6. **Decide by trust tier**:
   - T1: official organizer/ticketing page parsed deterministically → auto-apply.
   - T2: official page extracted by AI, confidence >= threshold, validation passes → auto-apply low-impact fields and auto-publish new events (marked auto-added); high-impact changes (date, status, location, registration URL) go to review.
   - T3: news/community/other → always review.
7. **Publish** to the public catalog; **audit log** every change; scheduled **link checker** flags dead registration links.
8. Refresh frequency scales with proximity of the event date; completed events are archived.

Thresholds and the high-impact field list are configuration.

## Alternatives considered
- Event-driven/real-time: unnecessary, data changes slowly.
- Organizer/community submissions only: sustainable but not automatic; kept as a supplementary channel.
- Social media scraping: fragile, terms and legal risk; rejected.
- Fully automatic with no review: risky for date/cancellation errors; rejected.

## Consequences
- Predictable, replayable, explainable; humans review only risky changes.
- Needs raw storage, scheduler, review queue and audit log.
- Source terms must be checked before enabling each source; candidates and findings in docs/DATA-SOURCES.md (robots.txt partly checked, ToS not yet).
- LLM cost and variance are bounded by caching raw docs, replay mode (runs without an API key) and call limits.

## AI involvement
AI proposed this model and the alternatives; the owner approved "scheduled + tiered trust". At runtime AI only extracts; deterministic rules validate.
