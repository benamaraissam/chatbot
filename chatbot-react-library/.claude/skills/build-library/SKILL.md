---
name: build-library
description: Use when the user wants to build the chatbot-react library, type-check it, or run the demo. Triggers include "vite build", "npm run build", "typecheck", or any React workflow validation in this repo.
---

# Building and validating chatbot-react

The library is built with `vite` in library mode (see `vite.config.ts`),
and types are emitted by `tsc -p tsconfig.build.json` before the vite build
runs.

## Common commands

```bash
# Install
npm install

# Run the demo at http://localhost:5173 against local src/
npm run dev

# Type-check only (no emit)
npm run typecheck

# Full library build (emits .d.ts + .js + .umd.cjs + .css)
npm run build

# Build the demo as a static site (for previewing UIs)
npm run build:demo
```

## Output contract

`npm run build` must produce, under `dist/`:

- `chatbot-react.js`        (ESM)
- `chatbot-react.umd.cjs`   (UMD)
- `chatbot-react.css`       (Tailwind output)
- `index.d.ts`              (types entry)

These paths are pinned in `package.json` `exports` and must not move.

## Troubleshooting

- "Cannot find module 'react'": `react` is a peer dep, you need to
  `npm install` to materialize the dev dep used for the demo.
- Tailwind classes missing in dist: check `tailwind.config.js` `content`
  globs include `src/**/*.{ts,tsx}`.
- Type errors only in build (not typecheck): `tsconfig.build.json` is
  stricter than `tsconfig.json` — fix the strict failures, do not loosen
  `tsconfig.build.json`.
