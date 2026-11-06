# Build with AI, Ship Right — Submission: RunDex

> Author: Huy Quang Nguyen · Individual challenge · Deadline: **2026-11-30 23:59** (files changed after are not counted)

## Submission map

| Requirement | Location |
|---|---|
| Source code | [`src/`](src/) |
| Documentation (what, key design decisions, how to run) | [`docs/`](docs/) |
| AI inputs (prompts, skills, agents, rules) | [`ai-inputs/`](ai-inputs/) |
| Steps to regenerate the code | [`REGENERATE.md`](REGENERATE.md) |
| Rules used with AI | [`CLAUDE.md`](CLAUDE.md) (copy in `ai-inputs/rules/`) |

## Reading order for reviewers
1. [`docs/OVERVIEW.md`](docs/OVERVIEW.md) — what was built and why
2. [`docs/DESIGN-DECISIONS.md`](docs/DESIGN-DECISIONS.md) — key decisions and trade-offs
3. [`docs/HOW-TO-RUN.md`](docs/HOW-TO-RUN.md) — run it in minutes
4. [`ai-inputs/README.md`](ai-inputs/README.md) — how AI was used
5. [`REGENERATE.md`](REGENERATE.md) — reproduce the code

## Layout
```
.
├── README.md
├── CLAUDE.md            # project rules (auto-update behaviour)
├── .claude/             # working copy of skills, agents, hooks
├── REGENERATE.md
├── src/                 # source code
├── docs/
│   ├── OVERVIEW.md
│   ├── DESIGN-DECISIONS.md
│   ├── DATA-SOURCES.md
│   ├── HOW-TO-RUN.md
│   ├── IMPLEMENTATION-PLAN.md
│   └── adr/             # one file per significant decision
├── ai-inputs/
│   ├── README.md
│   ├── PROMPT-LOG.md
│   ├── prompts/  skills/  agents/  rules/
└── scripts/
    ├── check-submission.sh   # pre-upload safety check
    └── sync-ai-inputs.sh     # .claude/ + CLAUDE.md -> ai-inputs/
```

Code repository: https://github.com/huynguyenquangce/RunDex

## Compliance
No client code, passwords, API keys or confidential data. Run `bash scripts/check-submission.sh` before uploading.
