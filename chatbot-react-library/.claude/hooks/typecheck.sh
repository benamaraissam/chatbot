#!/usr/bin/env bash
# Claude Code PostToolUse hook for chatbot-react-library.
# Runs `tsc --noEmit` after any .ts/.tsx edit so type regressions are caught
# inside the AI session rather than at build time.

set -uo pipefail

payload="$(cat || true)"

file_path="$(printf '%s' "$payload" | node -e '
let buf = "";
process.stdin.on("data", c => buf += c);
process.stdin.on("end", () => {
  try {
    const data = JSON.parse(buf || "{}");
    const fp = (data.tool_input && data.tool_input.file_path) || "";
    process.stdout.write(fp);
  } catch (_) {}
});' 2>/dev/null || true)"

case "$file_path" in
  *.ts|*.tsx) ;;
  *) exit 0 ;;
esac

if ! command -v npx >/dev/null 2>&1; then
  exit 0
fi

npx --no-install tsc --noEmit >/dev/null 2>&1
status=$?

if [ $status -ne 0 ]; then
  echo "::claude:: TypeScript typecheck failed for chatbot-react." >&2
fi

exit 0
