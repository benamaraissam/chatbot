# chatbot-python-library

Backend Python **framework-agnostic** pour chatbot agentic : multi-LLM, tools, MCP, streaming SSE.

Conforme au [plan d'architecture](../PLAN.md).

## Install from PyPI (public)

Once published:

```bash
pip install chatbot
pip install "chatbot[fastapi]"    # FastAPI router + SSE
pip install "chatbot[server]"     # CLI `chatbot serve`
pip install "chatbot[all]"        # all optional extras
```

Package name on PyPI: **`chatbot`** (see `name` in `pyproject.toml`).

## Install locally (editable / path)

For development in this repo or consuming the package from disk without publishing.

### Editable install (recommended for development)

```bash
cd chatbot-python-library
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[fastapi]"        # core + FastAPI
# pip install -e ".[all]"          # all extras
```

Changes under `src/chatbot/` are picked up immediately (no reinstall).

### Install from a local directory (another project)

```bash
pip install /absolute/path/to/chatbot-python-library
pip install "/path/to/chatbot-python-library[fastapi]"
```

### Install from Git (no PyPI)

```bash
pip install "git+https://github.com/YOUR_ORG/ChatBot.git#subdirectory=chatbot-python-library"
pip install "git+https://github.com/YOUR_ORG/ChatBot.git#subdirectory=chatbot-python-library[fastapi]"
```

## Publish to PyPI (public)

Uses [Hatchling](https://hatch.pypa.io/) (`pyproject.toml`).

1. **Create accounts** on [PyPI](https://pypi.org) and [TestPyPI](https://test.pypi.org) (optional but recommended for a dry run).

2. **Install build tools**:

   ```bash
   pip install hatch twine
   ```

3. **Run tests**:

   ```bash
   pip install -e ".[fastapi]"
   pytest tests/ -v
   ```

4. **Bump version** in `pyproject.toml` (`[project].version`, semver).

5. **Build artifacts**:

   ```bash
   cd chatbot-python-library
   hatch build
   # creates dist/chatbot-0.1.0.tar.gz and dist/chatbot-0.1.0-py3-none-any.whl
   ```

6. **Upload to TestPyPI first** (optional):

   ```bash
   twine upload --repository testpypi dist/*
   pip install --index-url https://test.pypi.org/simple/ chatbot
   ```

7. **Upload to PyPI**:

   ```bash
   twine upload dist/*
   ```

   Or with Hatch:

   ```bash
   hatch publish
   ```

   Use an API token from PyPI (`TWINE_USERNAME=__token__`, `TWINE_PASSWORD=pypi-...`).

8. **Consumers**:

   ```bash
   pip install chatbot
   pip install "chatbot[fastapi]"
   ```

**Note:** PyPI package names are global. If `chatbot` is already taken, change `name` in `pyproject.toml` (e.g. `your-org-chatbot`) before the first publish.

## Installation (this repo)

```bash
cd chatbot-python-library
pip install -e .                    # core
pip install -e ".[fastapi]"         # + adaptateur FastAPI
pip install -e ".[all]"             # tout
cp .env.example .env                # puis éditer OPENAI_API_KEY, etc.
pip install python-dotenv           # ou pip install -e ".[server]"
```

### Fichier `.env`

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Clé API (OpenAI, Moonshot, …) |
| `OPENAI_BASE_URL` | URL racine compatible OpenAI (ex. `https://api.moonshot.ai/v1`) |
| `CHATBOT_OPENAI_MODEL` | Modèle (ex. `kimi-k2.6`, `gpt-4o`) |
| `CHATBOT_DEFAULT_PROVIDER` | `mock` ou `openai` |
| `ANTHROPIC_API_KEY` | Optionnel, provider Claude |

`examples/02_web_apps/{fastapi,flask,django}_app.py` chargent automatiquement `chatbot-python-library/.env`.

| Extra | Contenu |
|-------|---------|
| `fastapi` | `create_router()` + SSE |
| `flask` | `create_blueprint()` |
| `django` | `chatbot_urls()` |
| `starlette` | routes ASGI |
| `postgres` | stockage PostgreSQL |
| `openapi` | `from_openapi()` |
| `litellm` | provider LiteLLM |
| `server` | CLI `chatbot serve` |

## Structure

```
src/chatbot/
├── core/           # AgentLoop, Chatbot, ToolContext, events
├── protocol/       # Schémas Pydantic + encodage SSE
├── providers/      # Anthropic, OpenAI, LiteLLM, Mock
├── tools/          # ToolRegistry, @http_tool, OpenAPI import
├── mcp/            # Client MCP + registry
├── storage/        # memory, SQLite, PostgreSQL
├── integrations/   # FastAPI, Flask, Django, Starlette, ASGI
├── server/         # Serveur standalone
└── cli.py
```

## Configuration YAML (serveur standalone)

Le CLI `chatbot serve` lit un fichier YAML (ou JSON). Copier l’exemple :

```bash
cp config.yaml.example config.yaml
pip install "chatbot[server]" pyyaml   # pyyaml requis pour .yaml
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
chatbot serve --config config.yaml --port 8000
```

Endpoint SSE : `POST http://localhost:8000/api/chat/chat`

### Exemple complet `config.yaml`

```yaml
host: "0.0.0.0"
port: 8000
default_provider: mock          # clé dans providers.*
system_prompt: "You are a helpful assistant."
storage: "sqlite:///./chatbot.db"   # ou "memory"
cors_origins:
  - "http://localhost:5173"
  - "http://127.0.0.1:5173"

providers:
  # Démo sans clé API
  mock:
    model: mock

  # Anthropic — noms d’alias : claude, anthropic
  claude:
    model: claude-sonnet-4-20250514
    api_key_env: ANTHROPIC_API_KEY

  # OpenAI officiel — alias : openai, gpt
  gpt:
    model: gpt-4o
    api_key_env: OPENAI_API_KEY
    # base_url: https://api.openai.com/v1
    # base_url_env: OPENAI_BASE_URL

  # Ollama / vLLM / gateway compatible OpenAI
  local:
    model: llama3.2
    base_url: http://localhost:11434/v1
    api_key_env: OPENAI_API_KEY   # souvent "ollama" ou vide selon le serveur

  # Azure OpenAI — alias : azure, azure_openai
  azure:
    model: gpt-4o-prod              # nom du déploiement Azure
    api_key_env: AZURE_OPENAI_API_KEY
    base_url_env: AZURE_OPENAI_ENDPOINT   # https://<resource>.openai.azure.com
    extra:
      api_version: "2024-10-21"

  # LiteLLM (100+ modèles) — pip install "chatbot[litellm]"
  # litellm:
  #   model: azure/gpt-4o
  #   api_key_env: AZURE_API_KEY
```

### Champs supportés

| Champ (racine) | Description |
|----------------|-------------|
| `host` / `port` | Bind du serveur FastAPI standalone |
| `default_provider` | Nom du provider utilisé si la requête HTTP ne précise pas de modèle |
| `system_prompt` | Instructions système pour l’agent |
| `storage` | `memory` ou `sqlite:///./chemin.db` |
| `cors_origins` | Origines autorisées pour le front React |
| `providers` | Map nom → réglages LLM (voir ci-dessous) |

| Champ (par provider) | Description |
|----------------------|-------------|
| `model` | Modèle par défaut pour ce provider (déploiement pour Azure) |
| `api_key` | Clé en dur (déconseillé en prod) |
| `api_key_env` | Nom de variable d’environnement pour la clé |
| `base_url` | URL racine ou complète (OpenAI-compatible) |
| `base_url_env` | Variable d’env pour l’URL |
| `extra` | Options spécifiques au provider (Azure : `api_version`, `use_aad`, `azure_ad_token`/`azure_ad_token_env`) |

> Le serveur standalone **ne charge pas les tools Python** du dossier `examples/` — il expose seulement le chat configuré. Pour des tools custom, utiliser FastAPI + `Chatbot(tools=...)` (voir plus bas).

---

## Providers (mode Python)

### Registre multi-provider

Chaque **clé** du dict `providers` est le nom que vous utilisez dans `default_provider` ou dans les requêtes. Le **type** de driver est déduit du nom ou du champ `model` :

| Clé config (`providers`) | Driver | Notes |
|--------------------------|--------|--------|
| `mock` ou `model: mock` | Mock | Démo, scénarios keyword (`thinking demo`, `weather`, …) |
| `claude`, `anthropic` | Anthropic | `ANTHROPIC_API_KEY` |
| `openai`, `gpt` | OpenAI-compatible | `OPENAI_API_KEY`, `base_url` |
| `azure`, `azure_openai` | Azure OpenAI | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `model` = nom de déploiement |
| `litellm` | LiteLLM | Extra `[litellm]` |

```python
from chatbot import Chatbot

bot = Chatbot(
    providers={
        "mock": {"model": "mock"},
        "claude": {
            "model": "claude-sonnet-4-20250514",
            "api_key_env": "ANTHROPIC_API_KEY",
        },
        "gpt": {
            "model": "gpt-4o",
            "api_key_env": "OPENAI_API_KEY",
        },
        "local": {
            "model": "llama3.2",
            "base_url": "http://localhost:11434/v1",
            "api_key_env": "OPENAI_API_KEY",
        },
    },
    default_provider="mock",
    system_prompt="You are a concise assistant.",
    storage="memory",  # ou "sqlite:///./data/chat.db"
    max_tool_rounds=10,  # LLM→tool→LLM rounds before the agent forces a wrap-up
)
```

**`max_tool_rounds`** caps how many LLM-call-then-tool-execute rounds the agent runs per user turn. Default 10 — handles paginated workflows comfortably. When the budget is hit, the agent makes one final no-tools call so the model produces a closing answer from whatever it has gathered. The user always gets a real reply; the `MessageEnd` event carries `finish_reason="max_tool_rounds"` for observability.

### OpenAI — URL et modèles personnalisés

Compatible **OpenAI**, **Ollama**, **vLLM**, gateways OpenAI-compatibles, etc.

`base_url` accepte :

- URL complète : `https://host/v1/chat/completions`
- Racine API : `https://host/v1` ou `https://host`
- Variable d’environnement : `base_url_env: OPENAI_BASE_URL`

### Azure OpenAI — déploiements + api-version

Driver natif (sans LiteLLM). `model` est le **nom du déploiement** Azure, et `base_url` l’endpoint de la ressource Azure :

```python
bot = Chatbot(
    providers={
        "azure": {
            "model": "gpt-4o-prod",            # nom du déploiement Azure
            "api_key_env": "AZURE_OPENAI_API_KEY",
            "base_url_env": "AZURE_OPENAI_ENDPOINT",   # https://<resource>.openai.azure.com
            "extra": {"api_version": "2024-10-21"},
        },
    },
    default_provider="azure",
)
```

URL construite automatiquement :
`https://<resource>.openai.azure.com/openai/deployments/<deployment>/chat/completions?api-version=<api_version>`

Override par requête possible (déploiement → modèle) :

```python
await bot.send("Hi", model="azure:gpt-4o-preview")     # autre déploiement
await bot.send("Hi", model="another-deployment")        # provider par défaut, déploiement override
```

**Authentification Entra ID (Azure AD) :**

```python
"azure": {
    "model": "gpt-4o-prod",
    "base_url_env": "AZURE_OPENAI_ENDPOINT",
    "extra": {
        "api_version": "2024-10-21",
        "use_aad": True,
        "azure_ad_token_env": "AZURE_OPENAI_AD_TOKEN",  # ou "azure_ad_token": "<token>"
    },
}
```

En AAD, l’en-tête `Authorization: Bearer <token>` est utilisé au lieu de `api-key`. Charge à l’app hôte de rafraîchir le token (via `DefaultAzureCredential` par ex.) et de l’exporter avant chaque appel — passer directement le token via `extra.azure_ad_token` au reboot suffit pour les déploiements statiques.

#### Variables d’environnement Azure

| Variable | Usage |
|----------|--------|
| `AZURE_OPENAI_ENDPOINT` | Endpoint de la ressource : `https://<resource>.openai.azure.com` |
| `AZURE_OPENAI_API_KEY` | Clé API du compte Azure OpenAI |
| `AZURE_OPENAI_API_VERSION` | API version (défaut `2024-10-21`) |
| `AZURE_OPENAI_AD_TOKEN` | Token Entra ID (mode AAD) |

#### Exemple YAML standalone

```yaml
providers:
  azure:
    model: gpt-4o-prod                # nom du déploiement
    api_key_env: AZURE_OPENAI_API_KEY
    base_url_env: AZURE_OPENAI_ENDPOINT
    extra:
      api_version: "2024-10-21"
```

### Choisir le modèle par requête

Sans changer la config globale :

```python
# Provider par défaut (default_provider)
await bot.send("Hello")

# Modèle exact configuré sur un provider
await bot.send("Hello", model="gpt-4o")

# Provider par son nom de registre
await bot.send("Hello", model="local")

# provider + modèle : "nom_registre:modele_api"
await bot.send("Hello", model="local:llama3.2")

# Modèle arbitraire sur le provider par défaut
await bot.send("Hello", model="gpt-4o-mini")
```

En HTTP (`ChatRequest`), le champ `model` suit les mêmes règles.

### LiteLLM

```bash
pip install "chatbot[litellm]"
export OPENAI_API_KEY=...
```

```python
bot = Chatbot(
    providers={
        "litellm": {
            "model": "gpt-4o",           # ou azure/..., bedrock/..., etc.
            "api_key_env": "OPENAI_API_KEY",
        },
    },
    default_provider="litellm",
)
```

### Variables d’environnement courantes

| Variable | Usage |
|----------|--------|
| `ANTHROPIC_API_KEY` | Provider `claude` / `anthropic` |
| `OPENAI_API_KEY` | Provider `openai` / `gpt` / souvent Ollama |
| `OPENAI_BASE_URL` | Si `base_url_env` est configuré |

---

## Usage rapide

### Mode librairie

```python
from chatbot import Chatbot, TextDelta

bot = Chatbot(default_provider="mock")  # ou "claude" avec ANTHROPIC_API_KEY

response = await bot.send("Hello", user_context={"user_id": "u_42"})
print(response.text)

async for event in bot.stream("Hello"):
    if isinstance(event, TextDelta):
        print(event.delta, end="", flush=True)
```

### FastAPI

```python
from fastapi import FastAPI
from chatbot import Chatbot
from chatbot.integrations.fastapi import create_router

bot = Chatbot(default_provider="mock")
app = FastAPI()
app.include_router(create_router(bot, user_context=get_user), prefix="/api/chat")
```

### Serveur standalone

```bash
cp config.yaml.example config.yaml
chatbot serve --config config.yaml --port 8000
```

## Protocole HTTP (v1)

`POST /chat` avec body JSON, réponse `text/event-stream`.

Header : `X-Chatbot-Protocol-Version: 1`

Événements SSE : `message_start`, `text_delta`, `tool_call_*`, `tool_result`, `message_end`, `error`, `done`.

## Tools

Les tools sont enregistrés dans un `ToolRegistry` passé à `Chatbot(tools=...)`. Le docstring et les annotations Python deviennent le schéma JSON pour le LLM.

### Enregistrement basique

```python
from chatbot import Chatbot, ToolRegistry
from chatbot.core.context import ToolContext

tools = ToolRegistry()

@tools.register
async def search_products(ctx: ToolContext, query: str, limit: int = 5) -> dict:
    """Search the product catalog."""
    return {"query": query, "items": [...]}

bot = Chatbot(tools=tools, default_provider="mock")
await bot.send("Find blue shoes", user_context={"user_id": "u_42"})
```

`ctx.user.id`, `ctx.secrets`, etc. sont disponibles via `ToolContext`.

### Options du décorateur `@tools.register`

```python
@tools.register(
    name="custom_name",           # défaut : nom de la fonction
    description="Override doc",   # défaut : docstring
    requires_approval=True,       # human-in-the-loop (UI React Approve/Deny)
    timeout=60.0,
    retry=2,
    cache_ttl=120.0,              # cache résultat (secondes)
    rate_limit_per_user=10,       # appels / minute / user
)
async def send_email(ctx, to: str, subject: str, body: str) -> dict:
    """Send email to a recipient."""
    ...
```

Après approbation côté client, renvoyer une requête avec `metadata.approvedToolIds: ["<tool_call_id>"]` (voir protocole SSE).

### Tools HTTP (`@http_tool`)

```python
from chatbot.tools import BearerAuth, http_tool, register_http_tools

@http_tool(
    method="GET",
    url="https://api.example.com/users/{user_id}",
    auth=BearerAuth(token_env="API_TOKEN"),
    timeout=15,
    retry=1,
)
async def get_user(user_id: str) -> dict:
    """Fetch user profile from CRM."""

tools = ToolRegistry()
register_http_tools(tools, get_user)
bot = Chatbot(tools=tools, default_provider="claude")
```

Voir `examples/05_with_http_tools.py`.

### Import OpenAPI → tools automatiques

```bash
pip install "chatbot[openapi]"
```

```python
from chatbot import Chatbot, ToolRegistry
from chatbot.tools import BearerAuth, from_openapi

tools = ToolRegistry()
tools.extend(
    from_openapi(
        spec_url="https://api.example.com/openapi.json",
        base_url="https://api.example.com",
        include=["listItems", "getItem"],  # optionnel : filtrer les opérations
        auth=BearerAuth(token_env="API_TOKEN"),
        timeout=20,
    )
)
bot = Chatbot(tools=tools, default_provider="claude")
```

Voir `examples/06_with_openapi_import.py`.

### Pagination & projection (`@paginated`)

Large API responses blow past LLM context windows. Wrap any list-returning tool with `@paginated` to (a) project each item to a small allowlist of fields, (b) expose `offset`/`limit` to the LLM so it can page on its own, and (c) return a stable envelope. Composes with any tool — HTTP, DB query, MCP wrapper, plain function.

```python
from chatbot import ToolRegistry, paginated

tools = ToolRegistry()

@tools.register
@paginated(
    items_path="$.fonds",                          # dotted path, callable, or None to auto-detect
    fields=("isin", "currency", "ytd", "nav"),     # allowlist; None = keep small scalars
    id_fields=("id", "isin", "ticker"),            # always preserved
    max_field_chars=200,                            # truncate long string values
    default_limit=25,
    max_limit=50,
    request_args=("profile", "language"),          # forward call kwargs into envelope
)
async def search_funds(ctx, profile: str = "PV_LU-FSE", language: str = "ENG") -> dict:
    """Search funds — `offset` and `limit` are injected into the tool schema automatically."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"https://api.example.com/funds/{profile}/{language}")
        r.raise_for_status()
        return r.json()
```

**Composing with `@http_tool`** — for a declarative tool with no body at all, stack `@paginated` over `@http_tool`. The decorator order matters (paginated outside, http_tool inside), and `@paginated` auto-disables `@http_tool`'s response cap so it can see the full payload:

```python
from chatbot import paginated
from chatbot.tools import http_tool

@tools.register
@paginated(
    fields=("isin", "currency", "ytd", "nav"),
    id_fields=("id", "isin", "ticker"),
    request_args=("profile", "language"),
)
@http_tool(
    method="GET",
    url="https://api.example.com/funds/{profile}/{language}",
    timeout=20.0,
    max_response_chars=None,    # @paginated will project + slice
)
async def search_funds(ctx, profile: str = "PV_LU-FSE", language: str = "ENG") -> dict:
    """Search funds — no body needed; the decorator stack does everything."""
```

If you reverse the order (`@http_tool` above `@paginated`), the library raises a clear `TypeError` — `@http_tool` replaces the function body, so pagination below it would be silently ignored.

**`request_args` vs `extra_scalars`** — both add scalar context to the envelope, but they pull from different places:

- `request_args=(...)` reads from the **call kwargs** of the wrapped function (with defaults applied). Use this for parameters the LLM passed (or could have passed) — it's what you want 95% of the time.
- `extra_scalars=(...)` reads from the **payload returned by the wrapped function**. Use only when the upstream response itself carries useful context that isn't available as a call arg (e.g. a server-computed `as_of_date`).

When both forward the same key, `request_args` wins. Neither can overwrite the reserved core envelope keys (`total`, `offset`, `limit`, `returned`, `has_more`, `items`).

Envelope returned to the LLM:

```json
{
  "total": 850,
  "offset": 0,
  "limit": 25,
  "returned": 25,
  "has_more": true,
  "items": [{ "isin": "FR0010135103", "currency": "EUR", "ytd": 8.42 }, ...],
  "profile": "PV_LU-FSE",
  "language": "ENG"
}
```

Why this beats the post-hoc `max_response_chars` truncation in `@http_tool`: with `@paginated` the LLM can ask for `offset=25` to see the next page; with truncation it just gets a `_truncated: true` marker and no way forward.

**Decorator order matters** — put `@paginated` *inside* `@tools.register` so the registry sees the augmented signature (with `offset`/`limit`).



```python
from chatbot import Chatbot
from chatbot.mcp import MCPServer

bot = Chatbot(
    mcp_servers=[
        MCPServer(name="github", command=["uvx", "mcp-server-github"]),
        MCPServer(name="remote", url="https://example.com/mcp/sse"),
    ],
    default_provider="claude",
    storage="memory",
)
# Les tools MCP sont chargés au premier send/stream
await bot.send("List open issues")
```

Voir `examples/07_with_mcp.py`.

### FastAPI avec tools (démo complète)

```python
from fastapi import FastAPI
from chatbot import Chatbot, ToolRegistry
from chatbot.integrations.fastapi import create_router

tools = ToolRegistry()

@tools.register
async def get_weather(ctx, city: str = "Paris") -> dict:
    """Return weather for a city."""
    return {"city": city, "temperature_c": 18, "condition": "sunny"}

@tools.register(requires_approval=True)
async def send_email(ctx, to: str, subject: str, body: str) -> dict:
    """Send email — requires approval in the UI."""
    return {"status": "sent", "to": to}

bot = Chatbot(
    providers={
        "mock": {"model": "mock"},
        "openai": {"model": "gpt-4o", "api_key_env": "OPENAI_API_KEY"},
    },
    default_provider="mock",  # or "openai"
    tools=tools,
    storage="memory",
)

app = FastAPI()
app.include_router(
    create_router(bot, user_context=lambda: {"user_id": "demo"}),
    prefix="/api/chat",
)
```

Lancer : `python examples/02_web_apps/fastapi_app.py` — aligné avec la démo React (`npm run dev`).

### Stockage des conversations

| Valeur `storage` | Comportement |
|------------------|--------------|
| `"memory"` | Historique en RAM (perdu au redémarrage) |
| `"sqlite:///./chatbot.db"` | Fichier SQLite local |
| DSN PostgreSQL | `pip install "chatbot[postgres]"` + DSN async |

```python
bot = Chatbot(storage="sqlite:///./data/conversations.db")
conv = bot.conversation(user_context={"user_id": "u1"})
await conv.send("First message")
await conv.send("Follow-up")  # même conversation_id
```

---

## Exemples

| Fichier | Description |
|---------|-------------|
| `examples/01_library_mode.py` | Mode librairie pur |
| `examples/02_web_apps/` | Apps FastAPI **+ Flask + Django** partageant `bot.py` & `tools.py` (8 patterns d'outils, 4 providers) |
| `examples/05_with_http_tools.py` | Tools HTTP |
| `examples/06_with_openapi_import.py` | Import OpenAPI |
| `examples/07_with_mcp.py` | Serveurs MCP |
| `examples/08_standalone_server.py` | Serveur standalone |

## Tests

```bash
pip install -e ".[fastapi]" pytest pytest-asyncio
pytest tests/ -v
```

## Flask en production (SSE)

Utiliser Gunicorn avec workers async :

```bash
gunicorn -k gevent -w 1 -b 0.0.0.0:5000 --chdir examples/02_web_apps flask_app:app
```

Ou migrer vers Quart pour l'async natif.

## Licence

MIT
