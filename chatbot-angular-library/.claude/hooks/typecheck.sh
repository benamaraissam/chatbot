#!/usr/bin/env bash
# Claude Code PostToolUse hook for chatbot-angular-library.
# Runs the TypeScript compiler in --noEmit mode against the library project
# whenever Claude edits a .ts file under projects/, surfacing type errors
# before they get committed.

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
  *.ts) ;;
  *) exit 0 ;;
esac

case "$file_path" in
  *projects/*) ;;
  *) exit 0 ;;
esac

if ! command -v npx >/dev/null 2>&1; then
  exit 0
fi

npx --no-install tsc -p projects/chatbot-angular/tsconfig.lib.json --noEmit >/dev/null 2>&1
status=$?

if [ $status -ne 0 ]; then
  echo "::claude:: TypeScript typecheck failed for the chatbot-angular library." >&2
fi

exit 0
