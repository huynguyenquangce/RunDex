---
name: log-prompt
description: Save a prompt (or skill/agent/rule) used to generate code into ai-inputs and add it to PROMPT-LOG.md. Use whenever AI is used to produce code or docs for the submission.
---

# log-prompt

Only for **key prompts**. Log one only if it (a) generated or substantially reshaped a major component, (b) drove a design/tech decision, (c) set up the AI workflow (rules/skills/agents), or (d) fixed a significant problem with a lesson worth keeping. Skip small edits, typo fixes, Q&A, clarifications and retries; when unsure, skip. Target ~5–15 entries overall.

1. Find the next number NN in `ai-inputs/prompts/` and create `NN-<slug>.md` from `_TEMPLATE.md`: date, tool/model, goal, exact prompt, result summary, manual fixes.
2. Add a row to `ai-inputs/PROMPT-LOG.md` (replace the placeholder row if it is still there).
3. If the prompt changed the generation procedure, update `REGENERATE.md`.
4. Redact secrets and confidential data before saving.
5. Run `bash scripts/sync-ai-inputs.sh` if skills/agents/rules changed.
