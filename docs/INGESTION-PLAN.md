# Ingestion plan: automatic discovery and updates

Status: accepted 2026-11-06 with the owner's decisions below; S1 done. Implements ADR 0003. The product ships no seed data: the database starts empty and this pipeline fills it.

## What "automatic" means here
A worker process that, on a schedule, (1) discovers event pages on registered sources, (2) fetches them politely, (3) extracts structured fields, (4) validates and compares them with what is stored, (5) applies safe changes and queues risky ones for a person. It runs wherever the database runs (docker compose locally; 24/7 only once hosted, see "Hosting").

```
sources.yaml -> discover URLs -> fetch (robots, rate limit, cache) -> raw_documents
   -> extract (JSON-LD, else LLM with quoted evidence) -> normalize -> validate (rules)
   -> match existing event (dedupe) -> diff -> change_proposals
   -> trust tier: auto-apply (+audit_log) | pending review (CLI) -> events
```

## Pieces
1. **Source registry** (`sources.yaml`, loaded into `sources`): `id, name, kind (sitemap | listing_page | event_page), url, tier (1|2|3), url_include (regex), refresh`. Adding a source is a config change.
2. **Discovery**: read a sitemap or listing page, keep URLs matching `url_include`, drop URLs already known and unchanged. Cheap heuristics first; the LLM only classifies ambiguous pages ("is this a running event page?"). Optional phase 2: LLM with web search to find new organizers (always tier 3, always reviewed).
3. **Fetcher**: honest User-Agent (`RunDexBot/0.1 (+repo URL)`), `robots.txt` via `urllib.robotparser`, about 1 request per 2 s per host, conditional GET (ETag/Last-Modified), size limit. Stores `raw_documents(source_id, url, fetched_at, status, content_hash, text)`; unchanged hash means skip extraction.
4. **Extractor** (adapter interface, three implementations):
   - `jsonld`: schema.org `Event`/`SportsEvent` blocks, deterministic (works only where a site publishes them; to be checked per source).
   - `llm`: Claude returns JSON for the event schema with per-field confidence and a **verbatim evidence quote**. A deterministic check drops any field whose quote does not occur in the page text (guards against invented values). Two ways to run it:
     - `api` mode: the worker calls the Claude API (needs `ANTHROPIC_API_KEY`, billed separately from a Claude chat/Code subscription); model `claude-haiku-5-5`. Fully automatic.
     - `assisted` mode (no key needed): the worker writes each page to `src/backend/data/inbox/<hash>.json`; the Claude Code subagent `event-extractor` (`.claude/agents/event-extractor.md`, Haiku) reads the inbox and writes `data/outbox/<hash>.json`; `ingest apply` loads the outbox through the same normalize, validate, diff and tier steps. Fetching, validation and applying stay automatic; only the extraction step needs a Claude Code run.
   - `replay`: returns recorded responses by content hash. Tests and reviewers run without an API key.
   The extractor returns 0..n candidates per page (a listing page holds many events). Output schema: see the agent file.
5. **Normalizer**: Vietnamese dates and numbers, `42K`/`42 km` to `distance_km`, fees in VND, province to the canonical list used by the region filter, slug `name-year`.
6. **Validator** (rules): name and start date present; dates sane; `end >= start`; distances positive; registration URL host equals the organizer host or an allowlisted ticketing platform; not a duplicate.
7. **Matcher/diff**: an existing event is the same if trigram similarity of name is high and dates are within 2 days (same province when known). Output: one `change_proposals` row per changed field (`old, new, confidence, evidence, source_url, status`).
8. **Decision by tier** (ADR 0003): T1 auto-apply; T2 auto-apply low-impact fields and new events, but date/status/location/registration URL changes go to review; T3 always review. Threshold and high-impact field list are config. Applied changes are written to `audit_log`. Auto-applied changes from an official source set `last_verified_at`; approved T3 changes set it at approval time.
9. **Review**: CLI first (`python -m app.ingest review | approve <id> | reject <id>`); screens later.
10. **Scheduler**: `python -m app.ingest run --once` and `worker` (loop). Refresh cadence by event date: within 30 days daily, within 180 days weekly, later monthly; discovery weekly. A `worker` service is added to docker compose.
11. **Link checker** (cut-line candidate): weekly HEAD request on `registration_url`, flag dead links.

## Data model additions (migration 0002)
`sources`, `raw_documents`, `change_proposals`, `audit_log` as in ADR 0004. No change to the public API.

## Configuration and secrets
`ANTHROPIC_API_KEY` and `LLM_MODEL` from the environment only (never committed; GitHub Secrets if a live run is ever added to CI). `INGEST_MODE=live|replay`. CI uses replay only.

## Work breakdown (hours, AI generates and I review)
| Slice | Output | h |
|---|---|---|
| S1 | Migration 0002, models, `sources.yaml` loader | 1.0 |
| S2 | Fetcher (robots, rate limit, conditional GET, storage) with tests on a mock transport | 1.0 |
| S3 | JSON-LD + LLM + replay extractors, evidence check, normalizers, tests | 1.5 |
| S4 | Validate, dedupe, diff, tier decision, apply + audit, tests | 1.0 |
| S5 | CLI (run, review, approve/reject), worker loop, compose service | 0.5 |
| S6 | ADR 0007, docs, architecture page | 0.5 |
About 5.5 h. Cut-line, in order: link checker, web-search discovery, review beyond CLI, second extractor type. Never cut: fetcher politeness, evidence check, validation, tier decision, audit log, tests.

## Honest limits
- Coverage equals the registered sources. Three organizer sites cover only a handful of events; broad coverage means adding many organizers over time, plus discovery.
- LLM extraction can still be wrong in ways the evidence check cannot catch (a correct quote read in the wrong context). That is why dates, status, place and links go to review unless the source is official and confidence is high.
- Without hosting, "automatic" runs only while the stack is up.

## Hosting
Out of scope for now (ADR to write if needed). Options: a PaaS plus a cloud PostgreSQL, a small VM, or the owner's own machine.

## Decisions (owner, 2026-11-06)
1. No API key for now: start with `replay` and `assisted` modes (agent `event-extractor`, model Haiku 5.5, i.e. `claude-haiku-5-5`); add the `api` provider behind the same interface when a key exists.
2. Sources: as many as possible; the registry `config/sources.yaml` starts with 19 (6 organizer/ticketing pages as tier 2, 11 listings and blogs as tier 3, 2 disabled with reasons). More are added over time. robots.txt is still checked at fetch time.
3. Review through the CLI for now.

## Progress
- S2 done: fetcher (robots.txt, 2 s per host, ETag, hash dedupe), sitemap discovery, `python -m app.ingest fetch`; real run on 17 sources queued 32 pages in `data/inbox`.
- S3 + S4 done (code and tests): `extract.py` (evidence check), `normalize.py`, `validate.py`, `match.py`, `changes.py` (diff + tier policy), `apply.py`, `pipeline.py`; CLI `apply`, `review`, `approve`, `reject`. Next: run the extractor agent on the inbox and `apply`.
- S1 done: migration 0002 (`sources`, `raw_documents`, `change_proposals`, `audit_log`), models, registry loader, `python -m app.ingest sources sync|list`, tests.

## Rules learned from the first real run (2026-11-06)
Run: 17 sources -> 32 pages -> 4 Haiku extractor agents -> 242 candidates. Outcome after the pipeline: 1 event applied automatically, 107 new events and 4 updates waiting for review, 85 duplicates merged, 48 rejected (24 dates not backed by the quote, 24 already finished).
- **Date must match its quote.** The day and month must appear in the quote and no other year may be named. A quote without a year means the year was inferred: the date is kept but its confidence is capped at 0.6, so it is never auto-applied. Month-only dates are rejected.
- **Omitted evidence vs invented evidence.** For descriptive fields (organizer, event type, province, venue, distances) a missing quote keeps the value as "unverified" (confidence 0.5, forces review); a quote that is not on the page drops the value.
- **Cross-source duplicates are merged** into one pending proposal with a note "also seen in: ..."; a better tier replaces a weaker pending proposal. Approving a create re-checks the catalog and supersedes it if the event now exists.
- **Finished events are not added** (the app only lists upcoming events).
- **Bulk review:** `review --summary`, `review --source/--kind/--min-confidence`, `approve --all <filters>`. Bulk approval stamps `last_verified_at` with the approval time, so approve in bulk only what you have looked at.
- Practical findings: only 5 of 107 pending events carry a registration link and about half have distances, because listing pages rarely give them; official event pages (tier 2) are what fill those fields.
- Extractor agent: in this run the agents were general-purpose Haiku agents following `.claude/agents/event-extractor.md` (the named agent is only loaded when a Claude Code session starts, so restart to use it by name). Two agents reported that quotes were not machine-checked: the pipeline check is the real test (24 dates were caught).

