# 02 — Ingestion model

- Date: 2026-11-06
- Tool/model: Claude Code (Sonnet 5.5)
- Goal: decide how event data is kept fresh and new events are discovered automatically.

## Prompt (condensed)
```
Data must update automatically and new running events must be added automatically. Which model? [after AI proposed: scheduled pull pipeline with tiered trust]
-> "Do scheduled scanning + tiered trust, and give me an overall of the project."
```

## Result summary
AI compared scheduled / event-driven / submission-only / social scraping; proposed a scheduled pipeline (registry -> fetch -> extract -> validate -> diff -> trust tier -> auto-apply or review). Outcome in ADR 0002, 0003, 0004 and docs/OVERVIEW.md.

## Manual fixes
Owner's requirement: automatic updates and discovery. Review thresholds and source list still to be decided by the owner.
