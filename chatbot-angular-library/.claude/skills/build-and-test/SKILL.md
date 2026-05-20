---
name: build-and-test
description: Use when the user wants to build the chatbot-angular library, run unit tests, or launch the demo app. Triggers include "ng build", "npm run build", "run the demo", or any Angular workflow validation in this repo.
---

# Building, testing, and running the demo

This Angular 17 workspace ships one publishable library
(`projects/chatbot-angular`) and one local demo app (`projects/demo`).

## Common commands

```bash
# Install
npm install

# Build the library (output: dist/chatbot-angular/)
npm run build

# Watch-mode build (for use with `npm link`)
npm run build:watch

# Run the demo app at http://localhost:4200
npm run demo

# Run the library's unit tests
npm test
```

## Workflow notes

- The demo app imports the library via TypeScript path mapping configured in
  `tsconfig.json`, so source changes are reflected immediately when the demo
  is running.
- After `npm run build`, the dist directory under `dist/chatbot-angular/`
  contains a publishable package that `ng-packagr` has generated according
  to `projects/chatbot-angular/ng-package.json`.
- Run `npm run build` once before opening a PR; CI runs the same command.

## Troubleshooting

- "Cannot find module '@angular/...'": run `npm install`.
- Stale build output: delete `dist/` and `.angular/cache/`, then rebuild.
- ng-packagr errors about secondary entry points: check
  `projects/chatbot-angular/ng-package.json` and ensure the entry exists.
