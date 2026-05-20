---
name: publish-to-npm
description: Use when the user wants to publish chatbot-angular to npm. Walks through version bumping, building from a clean tree, and the npm publish command.
---

# Publishing chatbot-angular to npm

The publishable artifact is produced by `ng-packagr` and lives in
`dist/chatbot-angular/` after a successful `npm run build`.

## Pre-flight

1. Confirm `git status` is clean — no uncommitted changes.
2. Bump the version in `projects/chatbot-angular/package.json` (not the
   workspace `package.json`, which is private).
3. Update CHANGELOG with the user-facing changes.

## Build and publish

```bash
# Build from a clean tree
rm -rf dist/ .angular/cache/
npm install
npm run build

# Inspect what will be published
cd dist/chatbot-angular
npm pack --dry-run

# Publish (requires `npm login` with publish rights)
npm publish --access public
```

## After publishing

1. Tag the release: `git tag v<version> && git push --tags`.
2. Open the npm page and confirm the published version matches.
3. Update the demo app to pin the new version if it consumes the library
   from npm rather than via path mapping.

Never publish from a dirty working tree or from `dist/` produced by
`build:watch` — only from a fresh `npm run build`.
