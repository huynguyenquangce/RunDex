#!/usr/bin/env bash
# Pre-upload check: required files present, no obvious secrets.
cd "$(dirname "$0")/.." || exit 1
fail=0
for f in README.md REGENERATE.md docs/OVERVIEW.md docs/DESIGN-DECISIONS.md docs/HOW-TO-RUN.md ai-inputs/README.md; do
  [ -f "$f" ] || { echo "MISSING: $f"; fail=1; }
done
[ -n "$(find src -path '*/node_modules' -prune -o -type f ! -name README.md ! -name .env.example -print 2>/dev/null | head -1)" ] || echo "WARN: src/ has no code yet"
grep -rIlE --exclude-dir=node_modules --exclude-dir=.git --exclude=check-submission.sh --exclude=package-lock.json \
  '(api[_-]?key|secret|password|token)["'"'"' ]*[:=]["'"'"' ]*[A-Za-z0-9_\-]{12,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY' . \
  && { echo "POSSIBLE SECRETS in files above"; fail=1; }
grep -rIn --exclude-dir=node_modules --exclude-dir=.git --exclude=check-submission.sh '_TBD_' . | head -1 >/dev/null && echo "WARN: unfilled _TBD_ placeholders remain"
[ $fail -eq 0 ] && echo "OK" || exit 1
