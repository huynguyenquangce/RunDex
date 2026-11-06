# CLAUDE.md — Project rules (RunDex)

## 1. Overview
"Build with AI, Ship Right" challenge submission. App name: RunDex. Individual work, deadline **2026-11-30 23:59**.
This folder IS the submission (see `README.md` for the 4 required outputs). Judged on design quality.
Idea: mobile app (iOS + Android, web later) that lists all running events in Vietnam; event detail view; organizer registration link as add-on; data updated and new events discovered automatically via a scheduled ingestion pipeline with tiered trust (see `docs/OVERVIEW.md`, ADR 0001–0005). Do not add product features beyond this scope without the owner's say-so.

## 2. Tech stack
Decided: PostgreSQL, FastAPI + worker/scheduler, Docker Compose (backend), mobile-first. Confirmed: Expo (React Native + TypeScript) for the app; GitHub Actions for CI. Monorepo (`src/backend`, `src/mobile`), repo https://github.com/huynguyenquangce/RunDex, ADR 0006; plan: docs/IMPLEMENTATION-PLAN.md. Never push client code or secrets. LLM behind an adapter with replay mode. See ADR 0005.

## 3. Commands
_TBD_ — keep in sync with `docs/HOW-TO-RUN.md`.
- Backend: `cd src && docker compose up --build`; tests `cd src/backend && pytest`; lint `ruff check . && ruff format --check .`
- Mobile: `cd src/mobile && npm install && npm start`; typecheck `npm run typecheck`; tests `npm test`; API types `npm run api:types`
- Pre-upload check: `bash scripts/check-submission.sh`
- Sync AI inputs: `bash scripts/sync-ai-inputs.sh`

## 4. Structure
- `src/` code · `docs/` documentation + `docs/adr/` · `ai-inputs/` prompts/skills/agents/rules · `REGENERATE.md`
- `.claude/` is the working copy of skills/agents/rules; `ai-inputs/` is the submitted snapshot (never edit it directly; run the sync script).

## 5. Conventions
- Language: talk to the user in **Vietnamese**; every file in this repo is in **English**.
- Code conventions: _TBD_ (style, naming, error handling, testing) — add once stack is chosen.
- Prefer simple, readable designs; justify every non-obvious choice in an ADR.

## 6. Workflow
1. Read relevant files before editing. Make the smallest change that solves the problem.
2. Run tests/lint (once they exist) before saying work is done.
3. Record key prompts as they happen (skill `log-prompt`), not afterwards; skip routine ones.
4. Before finishing a milestone, invoke agent `reviewer`.

## 7. Auto-update rules (IMPORTANT)
The user does NOT edit docs by hand. When the user decides or we discuss something that changes the project,
update the files yourself in the same turn, unasked:

| Trigger | Update |
|---|---|
| Idea / scope chosen or changed | `docs/OVERVIEW.md`, section 1 here |
| Design or tech decision | `docs/DESIGN-DECISIONS.md` + new ADR (skill `write-adr`); stack changes also update section 2 |
| Code added / structure changed | `src/README.md`, `README.md` layout |
| Setup/run/test commands change | `docs/HOW-TO-RUN.md`, section 3 here |
| A **key prompt** (see criteria below), or a skill/agent/rule used to generate code | skill `log-prompt` → `ai-inputs/prompts/` + `PROMPT-LOG.md` |
| Tools/model/workflow notes | `ai-inputs/README.md` |
| Generation steps / manual post-edits | `REGENERATE.md` |

- **Key prompts only.** Log a prompt only if it (a) generated or substantially reshaped a major component, (b) drove a design/tech decision, (c) set up the AI workflow (rules/skills/agents), or (d) fixed a significant problem with a lesson worth keeping. Do NOT log chores: small edits, typo fixes, Q&A, clarifications, retries. Keep it to roughly 5–15 entries in total.
- Replace `_TBD_` as soon as information exists; never leave stale content.
- Record manual fixes honestly (AI output vs. human change).
- After updating, say in one short line which files changed.
- After editing anything in `.claude/` or `CLAUDE.md`, run `bash scripts/sync-ai-inputs.sh`.

## 8. Do / Don't
- Do keep files short and skimmable; link instead of duplicating.
- Don't add dependencies without recording an ADR.
- Don't edit `ai-inputs/` by hand; don't modify files outside this folder.
- Don't claim something works without running it.

## 9. Safety
- Never write client code, passwords, API keys or confidential data in this folder.
- Run `bash scripts/check-submission.sh` before declaring anything ready to upload.
