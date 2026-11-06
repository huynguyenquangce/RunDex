#!/usr/bin/env bash
# Copy the working AI config (.claude/ + CLAUDE.md) into ai-inputs/ for submission.
cd "$(dirname "$0")/.." || exit 1
mkdir -p ai-inputs/skills ai-inputs/agents ai-inputs/rules
rm -rf ai-inputs/skills/* ai-inputs/agents/*
[ -d .claude/skills ] && cp -r .claude/skills/. ai-inputs/skills/
[ -d .claude/agents ] && cp -r .claude/agents/. ai-inputs/agents/
cp CLAUDE.md ai-inputs/rules/CLAUDE.md
[ -f .claude/settings.json ] && cp .claude/settings.json ai-inputs/rules/claude-settings.json
echo "ai-inputs synced"
