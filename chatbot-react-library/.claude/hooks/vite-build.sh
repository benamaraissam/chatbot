#!/usr/bin/env bash
# Claude Code Stop hook for chatbot-react-library.
# Runs `npm run build` once at end-of-turn so the reviewer sees whether the
# library still builds. Skipped if npm is unavailable.

set -uo pipefail

if ! command -v npm >/dev/null 2>&1; then
  exit 0
fi

[ -f package.json ] || exit 0

npm run build --silent >/dev/null 2>&1
status=$?

if [ $status -ne 0 ]; then
  echo "::claude:: vite build failed — chatbot-react no longer builds cleanly." >&2
fi

exit 0
