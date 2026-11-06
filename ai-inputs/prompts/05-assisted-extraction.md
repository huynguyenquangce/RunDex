# 05 — Extraction without an API key

- Date: 2026-11-06
- Tool/model: Claude Code (Sonnet 5.5); extractor agent runs on Haiku 5.5
- Goal: decide how event data is extracted when no Claude API key is available.

## Prompt (condensed)
```
Do I need a Claude API key? Can I just ask Claude in this chat to extract and inject the data manually?
Use claude-haiku-5.5, and have an agent do the extraction. Sources: as many as possible. Review via CLI is fine.
```

## Result summary
AI explained that the key is only needed for code that calls the API; proposed three extractor modes behind one interface (replay, assisted via a Claude Code subagent, api). Created `.claude/agents/event-extractor.md` (Haiku) with an evidence-mandatory output schema, and a 19-source registry. Recorded in docs/INGESTION-PLAN.md.

## Manual fixes / lessons
- Page text is untrusted: the agent is told to ignore instructions found in pages.
- A test run once reset the dev database; tests now refuse non-`*_test` databases.
