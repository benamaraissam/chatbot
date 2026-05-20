#!/usr/bin/env bash
# Claude Code Stop hook for chatbot-angular-library.
# Runs `npm run build` once at end-of-turn so the human reviewer sees whether
# the library still builds cleanly. Skipped if npm or ng are unavailable.

set -uo pipefail

if ! command -v npm >/dev/null 2>&1; then
  exit 0
fi

[ -f package.json ] || exit 0

npm run build --silent >/dev/null 2>&1
status=$?

if [ $status -ne 0 ]; then
  echo "::claude:: ng build failed — chatbot-angular no longer compiles cleanly." >&2
fi

exit 0
