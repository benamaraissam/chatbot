---
name: publish-to-npm
description: Use when the user wants to publish chatbot-react to npm. Walks through version bumping, building from a clean tree, and the npm publish command.
---

# Publishing chatbot-react to npm

`package.json` already declares `files: ["dist"]` and the correct `exports`
map, so a successful build is all that is needed before publishing.

## Pre-flight

1. Confirm `git status` is clean — no uncommitted changes.
2. Bump the version in `package.json`.
3. Update CHANGELOG with the user-facing changes.

## Build and publish

```bash
# Build from a clean tree
rm -rf dist/ node_modules/.vite
npm install
npm run typecheck
npm run build

# Inspect what will be published
npm pack --dry-run

# Publish (requires `npm login` with publish rights)
npm publish --access public
```

## After publishing

1. Tag the release: `git tag v<version> && git push --tags`.
2. Open the npm page and confirm the published version matches.
3. Verify the package installs cleanly into a sample React 17 and React 18
   project — peer dependency mismatches are the most common breakage.

Never publish from a dirty working tree, and never publish without running
`npm run typecheck` first.
