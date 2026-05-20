#!/usr/bin/env bash
# Claude Code PostToolUse hook for chatbot-python-library.
# Runs `ruff format` and `ruff check --fix` on any Python file Claude just
# edited or wrote, keeping AI-generated code consistent with the repo style.
#
# Hook input arrives on stdin as JSON with shape:
#   { "tool_input": { "file_path": "<absolute path>" }, ... }
# We extract file_path and only act on .py files inside this project.

set -euo pipefail

if ! command -v ruff >/dev/null 2>&1; then
  exit 0
fi

payload="$(cat || true)"

file_path="$(printf '%s' "$payload" | python -c 'import json,sys
try:
    data = json.loads(sys.stdin.read() or "{}")
except Exception:
    sys.exit(0)
fp = (data.get("tool_input") or {}).get("file_path") or ""
print(fp)' 2>/dev/null || true)"

case "$file_path" in
  *.py) ;;
  *) exit 0 ;;
esac

[ -f "$file_path" ] || exit 0

ruff format "$file_path" >/dev/null 2>&1 || true
ruff check --fix "$file_path" >/dev/null 2>&1 || true

exit 0
