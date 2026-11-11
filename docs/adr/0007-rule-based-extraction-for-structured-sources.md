# ADR 0007: Rule-based extraction for sources with structured data (pace8)

- Status: accepted
- Date: 2026-11-11

## Context
The owner chose pace8.vn as a data source. Every pace8 event page carries a schema.org `Event` JSON-LD block with name, dates, location, organizer and one offer per distance (price, sold out or not). An LLM adds cost and the risk of invented values on data that is already machine-readable.

## Decision
- A source can set `extractor: jsonld` in `config/sources.yaml` (default `ai`). Its pages are read by rules (`app/ingest/jsonld.py`) at fetch time and the result goes straight to `data/outbox`; pages without a usable Event fall back to the AI inbox.
- Every value is quoted from the page's JSON-LD text, so the normal verify, normalize, validate, match, diff and tier steps run unchanged.
- pace8 is **tier 2**: new events and fee changes are applied automatically; dates, status, location and links go to review. pace8 sells tickets but is not the organizer.
- All offers sold out means `registration_closed`. Offers that are not a plain distance (children's tickets) are ignored; the event type is only set when the name says trail, mountain, jungle or ultra.
- Source discovery uses the sitemap filtered to `/su-kien/<slug>`. Migration 0003 adds `sources.extractor`.

## Alternatives considered
- LLM extraction for pace8 as for blogs: slower, paid, can invent values; rejected for structured data.
- Tier 1 (apply everything): pace8 is a reseller and may lag the organizer; rejected.

## Consequences
- Fees per distance and sold-out state become available; start time, elevation and cut-off stay empty.
- Sold out is treated as closed registration, which is how it looks to a runner.
- Other sites with JSON-LD can be added by one line of config.

## AI involvement
AI proposed and implemented the extractor; the owner chose pace8 and asked AI to decide the rest.
