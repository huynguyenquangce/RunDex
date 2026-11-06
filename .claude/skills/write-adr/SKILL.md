---
name: write-adr
description: Record a design or technology decision as an Architecture Decision Record in docs/adr and update the decisions table. Use whenever a significant decision is made or changed.
---

# write-adr

1. List `docs/adr/` and pick the next 4-digit number. Copy `docs/adr/_TEMPLATE.md` to `NNNN-<slug>.md` (0001 is already used by the project-choice ADR).
2. Fill: Status, Date (today, YYYY-MM-DD), Context, Decision, Alternatives considered (at least 2, with pros/cons), Consequences, AI involvement (what AI suggested vs. what the human changed).
3. Add a row to the table in `docs/DESIGN-DECISIONS.md` linking the ADR. Remove the `_TBD_` row if present.
4. If the decision supersedes an earlier ADR, set the old one to `superseded` and link both ways.
5. Report the ADR path in one line.

Keep each ADR under ~40 lines. Be honest about trade-offs.
