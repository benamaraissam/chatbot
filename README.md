# ChatBot

Deux librairies indépendantes, conformes au [plan d'architecture](PLAN.md) :

| Dossier | Description |
|---------|-------------|
| [`chatbot-python-library/`](chatbot-python-library/) | Backend Python framework-agnostic (FastAPI, Flask, Django…) |
| [`chatbot-react-library/`](chatbot-react-library/) | Composants React embeddables (floating chat, SSE streaming) |

Chaque dossier est un projet autonome avec son propre `package.json` / `pyproject.toml`, versioning et publication (npm / PyPI).

## Installation & publication

| Package | Install (public) | Install (local) | Publish |
|---------|------------------|-----------------|---------|
| React (`chatbot-react`) | `npm install chatbot-react` | `npm link`, `file:../…`, or `npm pack` | [React README — Publish to npm](chatbot-react-library/README.md#publish-to-npm-public-registry) |
| Python (`chatbot`) | `pip install chatbot` | `pip install -e ".[fastapi]"` | [Python README — Publish to PyPI](chatbot-python-library/README.md#publish-to-pypi-public) |

Details, peer dependencies, and troubleshooting are in each library README.

## Démarrage rapide

**Backend Python** (`chatbot-python-library/`)

```bash
cd chatbot-python-library
python -m venv .venv && source .venv/bin/activate
pip install -e ".[fastapi]"
pytest tests/ -v
chatbot serve --config config.yaml.example --port 8000
```

**Lib React** (`chatbot-react-library/`)

```bash
cd chatbot-react-library
npm install
npm run build
npm run dev   # demo → http://localhost:5173
```
