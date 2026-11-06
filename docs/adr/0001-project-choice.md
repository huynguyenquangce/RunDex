# ADR 0001: Build a Vietnam running-events tracker

- Status: accepted
- Date: 2026-11-06

## Context
Challenge is judged on design by senior technical leaders; ~12 hours available (4h/week, 13–30 Nov); individual work; no client data allowed. The brief does not define a topic. I want a project with a real user pain, public data only, and room for good architecture, AI usage and UX.

## Decision
Build a web app that aggregates running events across Vietnam (all types) with AI-assisted ingestion and human verification.

## Alternatives considered
- IaC guardrail checker (DevOps/security): rejected, generic scanners (Checkov, tfsec) exist and AI self-checks cover common cases.
- RuleLoop (measure whether AI follows coding rules): strong design story, but less tied to my own domain knowledge; kept as fallback.
- PR risk dashboard, incident room: weaker demo data or scope risk.

## Consequences
- Hard part is data acquisition, not UI: avoid scraping Facebook; use user/organizer submissions, public pages and seed data.
- Wrong deadline data can harm users: needs source links, verification status and last-checked time.
- Design effort should go to the ingestion pipeline, confidence model, review queue and UX.

## AI involvement
AI proposed the idea shortlist and compared options; I rejected the DevOps ideas and chose the running tracker. AI ran a quick market search (see docs/OVERVIEW.md). Prompt logged as ai-inputs/prompts/01-project-selection.md.
