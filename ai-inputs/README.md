# AI Inputs

Everything used to generate the code, so the work is transparent and reproducible.

| Folder | Contents |
|---|---|
| `prompts/` | Prompts, numbered in execution order (`01-<topic>.md`) |
| `skills/` | Skill definitions used |
| `agents/` | Subagent / agent definitions |
| `rules/` | Rules files (e.g. CLAUDE.md, coding standards) |
| `PROMPT-LOG.md` | Chronological log: prompt → result → manual fix |

## Selection policy
Only key prompts are included: those that shaped major components, drove design decisions, set up the AI workflow, or solved significant problems. Routine prompts are intentionally omitted.

## Tools used
_TBD (tool, model, version)_

## Approach and workflow
_TBD (how AI was directed, reviewed and validated)_

> `skills/`, `agents/` and `rules/` are generated snapshots: edit `.claude/` and `CLAUDE.md`, then run `bash scripts/sync-ai-inputs.sh`.

> Redact any secret or confidential data before saving here.
