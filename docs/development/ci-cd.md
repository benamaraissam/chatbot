# CI / CD

Every push runs the test matrix; tag-driven workflows handle publishing.
All workflows live under [`.github/workflows/`](../../.github/workflows/).

## Continuous Integration

[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) runs on every
push to `main` and on every PR targeting `main`. Three independent jobs:

| Job | Runner | Steps |
|---|---|---|
| `test-python` | ubuntu-latest | `actions/setup-python@v5` (3.11) · `uv sync --group dev` · `ruff check src/` · `pytest` |
| `typecheck-react` | ubuntu-latest | `actions/setup-node@v4` (20) · `npm ci` · `npm run typecheck` · `npm test -- --run` · `npm run build` |
| `test-angular` | ubuntu-latest | `actions/setup-node@v4` (20) · `npm ci` · `npm test -- --watch=false --browsers=ChromeHeadless` · `npm run build` |

Each job's `working-directory` is set to its own library folder, so they
run cleanly side-by-side without interfering.

## Continuous Delivery

Three independent publish workflows, one per library, each driven by a
distinct tag prefix so they cannot fire on each other's releases.

### Python → PyPI

File: [`.github/workflows/publish-pypi.yml`](../../.github/workflows/publish-pypi.yml).

- **Triggers**: push of a tag matching `python-v*`, or a GitHub Release
  whose `tag_name` starts with `python-v`.
- **Gate**: a `decide` job checks the tag prefix and skips if it doesn't
  match. Additionally, when both `push: tags` and `release: published`
  fire for the same tag, only the release event proceeds — preventing a
  double-publish.
- **Steps**: install via `uv sync --group dev` → `ruff check src/` → `pytest` →
  derive version from the tag (strips `python-v` / `python-` / `v`) →
  `uv build` → `pypa/gh-action-pypi-publish` via **trusted publishing**
  (no token in repo secrets).

### React → npm

File: [`.github/workflows/publish-npm.yml`](../../.github/workflows/publish-npm.yml).

- **Triggers**: push of a tag matching `react-v*`, or a Release with that
  tag.
- **Gate**: tag-prefix check + dedup against the release event.
- **Steps**: `npm ci` → `npm run typecheck` → `npm run build` → sync
  version into `package.json` via `npm version` → `npm publish
  --provenance --access public`. Provenance attestation requires the
  `id-token: write` permission, which the workflow declares.
- **Secret**: `NPM_TOKEN` in repo secrets.

### Angular → npm

File: [`.github/workflows/publish-npm-angular.yml`](../../.github/workflows/publish-npm-angular.yml).

- **Triggers**: push of a tag matching `angular-v*`, or a matching Release.
- **Gate**: identical pattern.
- **Steps**: `npm ci` → run Karma tests headlessly → `npm run build` →
  bump version inside `projects/chatbot-angular/package.json` (not the
  workspace root) → rebuild → `npm publish` from the
  `projects/chatbot-angular/dist/` directory, with provenance.
- **Secret**: `NPM_TOKEN`.

## Release workflow

The recommended flow for each library:

```bash
# Python
cd chatbot-python-library
# bump version in pyproject.toml, update CHANGELOG, commit
git tag python-v0.2.0 && git push --tags
# OR create a GitHub Release with tag = python-v0.2.0

# React
cd chatbot-react-library
git tag react-v0.2.0 && git push --tags

# Angular
cd chatbot-angular-library
git tag angular-v0.2.0 && git push --tags
```

Either the `push: tags` event or a GitHub Release will trigger the publish
workflow — pick one. The gates make sure the same tag is not published
twice.

## How the tag-prefix gates work

Each publish workflow's first job (`decide`) reads `github.event.release.tag_name`
when triggered by a release, and `GITHUB_REF_NAME` when triggered by a tag
push. It then:

1. Returns `proceed=false` if the tag does not start with the library's
   prefix (so an `angular-v*` Release does not trigger the React publish).
2. When triggered by `push: tags`, checks if a Release already exists for
   the tag — if yes, the release event will publish and this run is
   skipped.

The `publish` job runs only when `proceed == 'true'`.

## Local pre-flight before tagging

```bash
# Python
cd chatbot-python-library
uv sync --group dev
ruff check src/
pytest
uv build && tar tzf dist/*.tar.gz | head -20

# React
cd chatbot-react-library
npm install
npm run typecheck && npm test -- --run && npm run build
npm pack --dry-run

# Angular
cd chatbot-angular-library
npm install
npm test -- --watch=false --browsers=ChromeHeadless
npm run build
cd projects/chatbot-angular/dist && npm pack --dry-run
```

The CI runs the same steps; the local commands let you fail fast.

## Coverage as a release gate (optional)

The unified coverage script (`make -C coverage coverage`) runs all three
libraries and writes a markdown + HTML report. If you want a release gate,
parse the `coverage-summary.json` files emitted by Istanbul/coverage.py and
fail the workflow if a library drops below a threshold. The script already
exits non-zero on test failure, so wiring this in is a small addition.

## See also

- [Testing](testing.md) — what the CI actually executes
- [Architecture](../architecture.md) — what each library produces
- [Python library](../libraries/python.md) — publish-to-PyPI details
- [React library](../libraries/react.md) — publish-to-npm details
- [Angular library](../libraries/angular.md) — publish-to-npm details
