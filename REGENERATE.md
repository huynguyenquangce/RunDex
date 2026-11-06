# Steps to Regenerate the Code

> Goal: a reviewer can reproduce `src/` from `ai-inputs/` with the same tools.

## Environment
- AI tool / version: _TBD_ (e.g. Claude Code vX)
- Model: _TBD_
- Other prerequisites: _TBD_

## Steps
1. Create an empty working directory and copy `ai-inputs/rules/` and `ai-inputs/skills/` into the tool's config location (_TBD_).
2. Run prompts in order from `ai-inputs/prompts/` (numbered `01-…`, `02-…`).
3. _TBD_ — any manual edits made after generation (list every one).
4. Verify using `docs/HOW-TO-RUN.md`.

## Notes on non-determinism
Output may differ between runs; record what was manually corrected and why.
