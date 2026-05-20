#!/usr/bin/env bash
# Claude Code Stop hook for chatbot-python-library.
# Runs the pytest suite once when Claude finishes a turn, so the human reviewer
# sees the test status alongside the diff.

set -uo pipefail

if ! command -v pytest >/dev/null 2>&1; then
  exit 0
fi

[ -d "tests" ] || exit 0

pytest tests/ -q --maxfail=1 --disable-warnings
status=$?

if [ $status -ne 0 ]; then
  echo "::claude:: pytest reported failures (exit $status) — review before claiming work complete." >&2
fi

exit 0
