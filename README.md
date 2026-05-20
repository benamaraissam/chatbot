# Chatbot Suite

A portable React (or Angular) embeddable chatbot UI talking to a
framework-agnostic Python backend over a stable HTTP + SSE protocol.

This monorepo holds three independently-versioned libraries that share one
wire protocol and one design system.

| Library | Folder | Package | Stack |
|---|---|---|---|
| Backend | [`chatbot-python-library/`](chatbot-python-library/) | PyPI · `chatbot` | Python 3.11+, FastAPI / Flask / Django / Starlette adapters |
| React | [`chatbot-react-library/`](chatbot-react-library/) | npm · `chatbot-react` | React 17/18, Vite, Tailwind |
| Angular | [`chatbot-angular-library/`](chatbot-angular-library/) | npm · `chatbot-angular` | Angular 17, standalone components |

## 5-minute quickstart

**Backend** — pick any one of FastAPI / Flask / Django / Starlette, or run the standalone server:

```bash
cd chatbot-python-library
python -m venv .venv && source .venv/bin/activate
pip install -e ".[fastapi]"
export ANTHROPIC_API_KEY=sk-ant-...
chatbot serve --config config.yaml.example --port 8000
```

**React frontend**:

```bash
cd chatbot-react-library && npm install && npm run dev   # http://localhost:5173
```

**Angular frontend** (alternative):

```bash
cd chatbot-angular-library && npm install && npm run demo   # http://localhost:4200
```

## Documentation

The full documentation lives in [`docs/`](docs/):

- [Overview & reading order](docs/README.md)
- [Architecture](docs/architecture.md)
- [Getting started](docs/getting-started.md)
- [Wire protocol](docs/wire-protocol.md)
- [Python backend guide](docs/libraries/python.md)
- [React library guide](docs/libraries/react.md)
- [Angular library guide](docs/libraries/angular.md)
- [Testing](docs/development/testing.md) · [CI / CD](docs/development/ci-cd.md) · [Claude in development](docs/development/claude.md)
- [Contributing](docs/contributing.md)
- [Phased roadmap](docs/PLAN.md)

## Tests + coverage

A single command runs the test matrix across all three libraries and writes
a consolidated HTML + Markdown report:

```bash
make -C coverage coverage   # all three
make -C coverage open       # open coverage/report.html
make -C coverage help       # list all targets
```

See [`docs/development/testing.md`](docs/development/testing.md) for details.

## License

MIT — see each library's `pyproject.toml` / `package.json` for the canonical declaration.
