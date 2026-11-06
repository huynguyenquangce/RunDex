# Key Design Decisions

Summarize the most important decisions here; detail goes in [`adr/`](adr/).

| # | Decision | Alternatives considered | Why | ADR |
|---|---|---|---|---|
| 1 | Build a Vietnam running-events tracker (all event types) | IaC guardrail, RuleLoop, PR risk dashboard | Real user pain, public data, room for ingestion/AI/UX design | [0001](adr/0001-project-choice.md) |
| 2 | Product scope: list + detail view, organizer link as add-on; automated data upkeep | Static hand-edited site; full platform | Fits ~12h, avoids competing with organizer platforms, automation is the real value | [0002](adr/0002-single-purpose-scope.md) |
| 3 | Scheduled ingestion pipeline with tiered trust | Event-driven; submissions only; social scraping; fully automatic | Predictable, explainable, humans review only risky changes | [0003](adr/0003-ingestion-model.md) |
| 4 | Event/Distance model with provenance, change proposals, audit log | Flat event row; full event sourcing | Per-distance data, traceable values | [0004](adr/0004-data-model.md) |
| 5 | PostgreSQL from day one; mobile-first (iOS + Android), web later; Expo confirmed | SQLite first; Flutter; native x2; web-first | Owner priority; Postgres fits jobs and unaccent search; one codebase for both stores | [0005](adr/0005-postgres-and-mobile-first.md) |
| 6 | Monorepo on GitHub, FastAPI/SQLAlchemy, Expo + TanStack Query, generated API types, GitHub Actions CI; EAS deferred | Separate repos; hand-written client types | One clone runs everything; contract drift caught in CI | [0006](adr/0006-engineering-stack-and-ci.md) |

## Trade-offs and known limitations
_TBD_

## What I would do next
_TBD_
