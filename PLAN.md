# Plan v3 — Chatbot React (lib npm) + Backend Python (lib + intégrations framework)

> **Stack** : Lib React (Vite + Tailwind préfixé) + Backend Python **library-first** avec adaptateurs **FastAPI / Flask / Django / ASGI** — Multi-LLM, MCP-ready, tools API natifs, open-source.

> **Changements v3** :
> - Backend Python utilisable comme **librairie embarquée** dans n'importe quelle app Python
> - Adaptateurs prêts à l'emploi pour **FastAPI**, **Flask**, **Django**, **Starlette/ASGI**
> - Support natif des **tools faisant des appels API** (HTTP, OpenAPI auto-import, auth per-user)

---

## 1. Vision du projet

Une **librairie React** qui s'intègre dans n'importe quel site existant, affiche un chatbot flottant moderne, et communique avec un **backend Python agentic** qui peut s'intégrer dans n'importe quelle application Python existante (Flask, FastAPI, Django, scripts, notebooks, Celery workers…).

**Pas un serveur fermé** : un cœur réutilisable + des adaptateurs.

Le backend supporte :
- Plusieurs LLM (Claude, OpenAI, Gemini, Ollama…) via PydanticAI/LiteLLM
- Tools custom (Python pur, HTTP/REST, OpenAPI auto-import)
- Serveurs MCP (Notion, GitHub, Slack…)
- Auth per-user pour les tools (OAuth tokens, API keys scoped)
- Streaming token par token + tool calls en temps réel

**Différenciation vs la concurrence** :
- Lib React vraiment portable, pas couplée à Next.js
- Backend Python **framework-agnostic** (FastAPI, Flask, Django…)
- MCP natif + tools API faciles à créer
- Protocole de communication ouvert et documenté

---

## 2. Architecture globale

```
┌──────────────────────────────────────────────────┐
│  Site React de l'utilisateur final                │
│  <ChatbotProvider> + <FloatingChatbot />          │
└────────────────────┬─────────────────────────────┘
                     │ HTTPS + SSE (protocole standard)
                     ▼
┌──────────────────────────────────────────────────┐
│  Backend Python — architecture en couches         │
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │ Layer 4 : Adaptateurs framework (extras)   │  │
│  │  ├─ integrations/fastapi.py                │  │
│  │  ├─ integrations/flask.py                  │  │
│  │  ├─ integrations/django.py                 │  │
│  │  ├─ integrations/starlette.py              │  │
│  │  └─ integrations/asgi.py                   │  │
│  ├────────────────────────────────────────────┤  │
│  │ Layer 3 : Standalone server CLI (optionnel)│  │
│  │  → uvicorn-based, prêt à l'emploi          │  │
│  ├────────────────────────────────────────────┤  │
│  │ Layer 2 : SDK Python public                │  │
│  │   Chatbot.send() / .stream()               │  │
│  │   bot.handle_request(req, user_context)    │  │
│  ├────────────────────────────────────────────┤  │
│  │ Layer 1 : Core (pur Python async)          │  │
│  │   AgentLoop · ToolRegistry · MCPClient     │  │
│  │   Providers · Storage · UserContext        │  │
│  └────────────────────────────────────────────┘  │
└────────────────────┬─────────────────────────────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        ▼            ▼            ▼              ▼
     Claude       OpenAI       Gemini         Ollama
                            +
     MCP servers · Tools API (REST/GraphQL) · DB · OAuth
```

---

## 3. Modes d'intégration du backend

### Mode A — Dans une app FastAPI existante

```python
from fastapi import FastAPI, Depends
from tonpackage_chatbot import Chatbot, ToolRegistry
from tonpackage_chatbot.integrations.fastapi import create_router

app = FastAPI()  # ton app existante

tools = ToolRegistry()
# ... register tools ...

bot = Chatbot(provider="claude", tools=tools)

# Une ligne pour brancher le chatbot
app.include_router(
    create_router(bot, auth=Depends(my_auth)),
    prefix="/api/chat",
    tags=["chatbot"],
)
```

### Mode B — Dans une app Flask existante

```python
from flask import Flask
from tonpackage_chatbot import Chatbot
from tonpackage_chatbot.integrations.flask import create_blueprint

app = Flask(__name__)  # ton app existante

bot = Chatbot(provider="claude", tools=tools)

# Blueprint Flask classique
app.register_blueprint(
    create_blueprint(bot, auth_decorator=login_required),
    url_prefix="/api/chat",
)
```

> ⚠️ **Note Flask** : pour le streaming SSE en prod, utiliser gunicorn avec workers `gevent` ou `eventlet`, ou passer à Quart. Documenté dans la doc avec config prête à copier.

### Mode C — Dans Django

```python
# urls.py
from django.urls import path, include
from tonpackage_chatbot import Chatbot
from tonpackage_chatbot.integrations.django import chatbot_urls

bot = Chatbot(provider="claude", tools=tools)

urlpatterns = [
    path("api/chat/", include(chatbot_urls(bot))),
]
```

### Mode D — En librairie pure (notebook, script, Celery, CLI)

```python
from tonpackage_chatbot import Chatbot

bot = Chatbot(provider="claude", tools=tools)

# Mode simple
response = await bot.send("Analyse ce dataframe", context={"df": df})
print(response.text)

# Mode streaming
async for event in bot.stream("Génère un rapport"):
    if event.type == "text_delta":
        print(event.delta, end="", flush=True)
```

### Mode E — Serveur standalone (zero-config)

```bash
tonpackage-chatbot serve --config config.yaml --port 8000
```

---

## 4. Packaging Python (extras)

```toml
# pyproject.toml
[project]
name = "tonpackage-chatbot"
dependencies = [
  "pydantic-ai>=0.0.x",
  "httpx>=0.27",
  "tenacity>=8.0",
  "mcp>=0.1",
  "pydantic>=2.0",
]

[project.optional-dependencies]
fastapi = ["fastapi>=0.100", "sse-starlette>=2.0"]
flask = ["flask>=2.3"]
django = ["django>=4.2", "channels>=4.0"]
starlette = ["starlette>=0.30", "sse-starlette>=2.0"]
postgres = ["asyncpg>=0.29"]
redis = ["redis>=5.0"]
openapi = ["openapi-pydantic>=0.4"]
server = ["fastapi>=0.100", "sse-starlette>=2.0", "uvicorn[standard]>=0.27"]
all = ["tonpackage-chatbot[fastapi,flask,django,postgres,redis,openapi,server]"]

[project.scripts]
tonpackage-chatbot = "tonpackage_chatbot.cli:main"
```

Install ciblé :
- `pip install tonpackage-chatbot` → core pur
- `pip install tonpackage-chatbot[fastapi]` → + adaptateur FastAPI
- `pip install tonpackage-chatbot[flask]` → + adaptateur Flask
- `pip install tonpackage-chatbot[all]` → tout

---

## 5. Tools — système complet

### 5.1 Catégories de tools supportés

**Tools internes (Python pur)** :
```python
@tools.register
async def get_user_orders(ctx: ToolContext, user_id: str, limit: int = 10) -> list[dict]:
    """Récupère les commandes d'un utilisateur."""
    return await db.fetch_orders(user_id, limit)
```

**Tools API HTTP — via decorator `@http_tool`** :
```python
from tonpackage_chatbot.tools import http_tool, BearerAuth

@http_tool(
    method="GET",
    url="https://api.weather.com/v1/{city}",
    auth=BearerAuth(token_env="WEATHER_API_KEY"),
    timeout=10,
    retry=3,
)
async def get_weather(city: str) -> dict:
    """Récupère la météo d'une ville."""
```

**Tools API HTTP — manuels avec httpx** :
```python
@tools.register
async def search_stripe_customers(ctx: ToolContext, email: str) -> list[dict]:
    """Cherche des clients Stripe par email."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://api.stripe.com/v1/customers",
            params={"email": email},
            headers={"Authorization": f"Bearer {ctx.secrets.stripe}"},
        )
        r.raise_for_status()
        return r.json()["data"]
```

**Tools depuis spec OpenAPI** (génération auto) :
```python
from tonpackage_chatbot.tools import from_openapi, BearerAuth

stripe_tools = from_openapi(
    spec_url="https://raw.githubusercontent.com/stripe/openapi/master/spec3.json",
    base_url="https://api.stripe.com",
    auth=BearerAuth(token_env="STRIPE_API_KEY"),
    include=["customers.*", "invoices.list", "subscriptions.*"],
    exclude=["*.delete"],
)
tools.extend(stripe_tools)
```

**Tools MCP** (zero-code, juste connexion) :
```python
from tonpackage_chatbot.mcp import MCPServer

mcp_servers = [
    MCPServer(name="notion", url="https://mcp.notion.com/sse"),
    MCPServer(name="github", command=["uvx", "mcp-server-github"]),
]
```

### 5.2 Mécanismes transverses (built-in)

- **Retry / backoff** automatique (via tenacity)
- **Timeout** par tool
- **Rate limiting** par tool et par user
- **Caching** opt-in
- **Approval flow** : `requires_approval=True` → l'UI demande confirmation
- **Logging / tracing** : hooks OpenTelemetry, Langfuse
- **Auth context per-user** via `ToolContext`

### 5.3 Auth per-user dans les tools

```python
@tools.register
async def list_my_gmail(ctx: ToolContext, max_results: int = 20) -> list[dict]:
    """Liste mes emails Gmail."""
    token = await ctx.user.oauth_token("gmail")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers={"Authorization": f"Bearer {token}"},
            params={"maxResults": max_results},
        )
        return r.json()["messages"]
```

Le `ToolContext` contient :
- `ctx.user.id` — identité du user (transmise via `user_context`)
- `ctx.user.oauth_token(provider)` — OAuth scoped
- `ctx.secrets.*` — secrets globaux
- `ctx.conversation_id` — id de conversation
- `ctx.metadata` — metadata libre

L'app hôte fournit un `UserContextProvider` qui résout ces infos depuis sa propre base d'auth.

---

## 6. Stack technique détaillée

### Frontend (lib React)

| Composant | Choix |
|-----------|-------|
| Build | Vite mode library |
| Langage | TypeScript |
| Styling | Tailwind CSS avec préfixe `cb-` |
| State | Zustand |
| Streaming | `fetch` + ReadableStream (SSE) |
| Markdown | `react-markdown` + `remark-gfm` |
| Code highlight | `shiki` |
| Animations | `framer-motion` |
| Icônes | `lucide-react` |

### Backend (package Python)

| Composant | Choix | Pourquoi |
|-----------|-------|----------|
| Core agent | **PydanticAI** | Async, typé, agentic-first |
| Multi-provider | PydanticAI + LiteLLM (fallback) | 100+ modèles |
| MCP | `mcp` SDK officiel Python | Standard Anthropic |
| Validation | Pydantic v2 | Schémas partagés client/serveur |
| HTTP tools | `httpx` async | Standard |
| Retry | `tenacity` | Robustesse |
| FastAPI adapter | `fastapi` + `sse-starlette` | SSE natif async |
| Flask adapter | `flask` (>= 2.3) + generator streaming | Compat sync/async |
| Django adapter | `django` + `channels` (SSE via ASGI) | Streaming moderne |
| Storage | Adapter pattern, SQLite par défaut | Pluggable |
| OpenAPI import | `openapi-pydantic` | Génération tools |

---

## 7. Protocole de communication

### 7.1 Requête (HTTP)

`POST /chat` :
```json
{
  "messages": [
    { "id": "msg_1", "role": "user", "parts": [{ "type": "text", "text": "Hello" }] }
  ],
  "conversationId": "conv_abc123",
  "model": "claude-opus-4-7",
  "metadata": { "userId": "user_42" }
}
```

### 7.2 Réponse serveur (SSE)

| Event | Payload |
|-------|---------|
| `message_start` | `{ id, role }` |
| `text_delta` | `{ delta }` |
| `tool_call_start` | `{ id, name, input }` |
| `tool_call_delta` | `{ id, inputDelta }` |
| `tool_call_end` | `{ id }` |
| `tool_result` | `{ id, output, isError }` |
| `tool_approval_required` | `{ id, name, input }` |
| `message_end` | `{ usage, finishReason }` |
| `error` | `{ code, message }` |
| `done` | `{}` |

### 7.3 Équivalent en mode librairie (async iterator)

```python
async for event in bot.stream("Hello"):
    match event:
        case TextDelta(delta=d):
            print(d, end="", flush=True)
        case ToolCallStart(name=name, input=inp):
            print(f"\n→ {name}({inp})")
        case ToolResult(output=out):
            print(f"  ← {out}")
```

Les adaptateurs framework transforment cet iterator en SSE/WebSocket.

---

## 8. Structure des packages

### 8.1 Lib React

```
chatbot-react/
├── src/
│   ├── components/         # FloatingButton, ChatWindow, MessageList...
│   ├── hooks/              # useChatbot, useStreamingChat, useConversation
│   ├── transport/          # sseClient, protocol types
│   ├── core/               # ChatbotProvider, store Zustand
│   ├── styles/             # globals.css, tokens.css
│   ├── utils/
│   ├── types/
│   └── index.ts
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

### 8.2 Backend Python

```
tonpackage-chatbot/
├── src/tonpackage_chatbot/
│   ├── __init__.py                     # Exports : Chatbot, ToolRegistry...
│   │
│   ├── core/                           # Layer 1 — pure async
│   │   ├── agent.py                    # AgentLoop (PydanticAI)
│   │   ├── chatbot.py                  # Classe Chatbot publique
│   │   ├── context.py                  # ToolContext, UserContext
│   │   └── events.py                   # Types streaming
│   │
│   ├── protocol/
│   │   ├── schemas.py                  # Schémas Pydantic
│   │   └── sse.py                      # Encodage SSE
│   │
│   ├── providers/
│   │   ├── base.py
│   │   ├── anthropic.py
│   │   ├── openai.py
│   │   └── litellm.py
│   │
│   ├── tools/
│   │   ├── registry.py                 # ToolRegistry
│   │   ├── http.py                     # @http_tool
│   │   ├── openapi.py                  # from_openapi()
│   │   ├── auth.py                     # BearerAuth, OAuth2Auth
│   │   └── builtin/
│   │       ├── web_search.py
│   │       └── code_interpreter.py
│   │
│   ├── mcp/
│   │   ├── client.py
│   │   └── registry.py
│   │
│   ├── storage/
│   │   ├── base.py
│   │   ├── memory.py
│   │   ├── sqlite.py
│   │   └── postgres.py
│   │
│   ├── integrations/                   # Layer 4 — adaptateurs
│   │   ├── fastapi.py                  # create_router(bot)
│   │   ├── flask.py                    # create_blueprint(bot)
│   │   ├── django.py                   # chatbot_urls(bot)
│   │   ├── starlette.py
│   │   └── asgi.py
│   │
│   ├── server/                         # Layer 3 — standalone
│   │   ├── app.py
│   │   └── config.py
│   │
│   └── cli.py
│
├── examples/
│   ├── 01_library_mode.py
│   ├── 02_fastapi_app.py
│   ├── 03_flask_app.py
│   ├── 04_django_project/
│   ├── 05_with_http_tools.py
│   ├── 06_with_openapi_import.py
│   ├── 07_with_mcp.py
│   └── 08_standalone_server.py
│
├── tests/
├── pyproject.toml
└── README.md
```

---

## 9. API publique côté Python

### 9.1 Création d'un Chatbot

```python
from tonpackage_chatbot import Chatbot, ToolRegistry
from tonpackage_chatbot.tools import http_tool, from_openapi
from tonpackage_chatbot.mcp import MCPServer

# 1. Tools
tools = ToolRegistry()

@tools.register
async def search_products(ctx, query: str) -> list[dict]:
    """Search the product catalog."""
    return await db.search(query)

@http_tool(method="GET", url="https://api.weather.com/v1/{city}")
async def get_weather(city: str) -> dict:
    """Get weather for a city."""

tools.extend(from_openapi(spec_url="...", base_url="..."))

# 2. MCP servers
mcp_servers = [
    MCPServer(name="notion", url="https://mcp.notion.com/sse"),
]

# 3. Chatbot
bot = Chatbot(
    providers={
        "claude": {"model": "claude-opus-4-7", "api_key_env": "ANTHROPIC_API_KEY"},
        "gpt": {"model": "gpt-4o", "api_key_env": "OPENAI_API_KEY"},
    },
    default_provider="claude",
    tools=tools,
    mcp_servers=mcp_servers,
    system_prompt="You are a helpful assistant for...",
    storage="sqlite:///./chatbot.db",
)
```

### 9.2 Utilisation directe (librairie)

```python
# One-shot
response = await bot.send("Hello", user_context={"user_id": "u_42"})
print(response.text)

# Streaming
async for event in bot.stream("Hello", user_context={"user_id": "u_42"}):
    ...

# Multi-turn manuel
conv = bot.conversation(id="conv_abc")
await conv.send("Hi")
await conv.send("What did I just say?")
```

### 9.3 Intégration FastAPI

```python
from fastapi import FastAPI, Depends
from tonpackage_chatbot.integrations.fastapi import create_router

app = FastAPI()

def get_user_context(user=Depends(current_user)):
    return {"user_id": user.id, "email": user.email}

app.include_router(
    create_router(bot, user_context=get_user_context),
    prefix="/api/chat",
)
```

### 9.4 Intégration Flask

```python
from flask import Flask
from flask_login import login_required, current_user
from tonpackage_chatbot.integrations.flask import create_blueprint

app = Flask(__name__)

def get_user_context():
    return {"user_id": current_user.id, "email": current_user.email}

bp = create_blueprint(
    bot,
    user_context=get_user_context,
    decorators=[login_required],
)
app.register_blueprint(bp, url_prefix="/api/chat")
```

### 9.5 Intégration Django

```python
# urls.py
from django.urls import path, include
from tonpackage_chatbot.integrations.django import chatbot_urls

def get_user_context(request):
    return {"user_id": request.user.id, "email": request.user.email}

urlpatterns = [
    path("api/chat/", include(chatbot_urls(bot, user_context=get_user_context))),
]
```

---

## 10. Fonctionnalités UI

### MVP
- Floating button + chat window slide-up
- Streaming token par token
- Markdown + code blocks avec copy
- Affichage tool calls (collapsible)
- Mode sombre/clair auto
- Mobile responsive (full-screen)
- Historique localStorage

### V2
- File upload (images, PDFs)
- Voice input (Web Speech API)
- Citations & sources (RAG)
- Quick replies / suggestions
- Feedback 👍/👎
- Multi-conversation (sidebar)
- Recherche dans l'historique
- Export conversation (md/PDF)
- **Approval flow UI** pour tools sensibles

### V3
- Generative UI (composants riches renvoyés par le LLM)
- Connector picker UI (MCP onboarding visuel)
- Webhooks pour events
- Plugin system

---

## 11. Roadmap par phases

### Phase 1 — Foundation (2 semaines)
- Monorepo setup (pnpm workspaces)
- Protocole défini (types TS + Pydantic)
- Lib React MVP : Provider + composants de base
- Backend Python : core + Chatbot + 1 provider (Claude)
- Adaptateur FastAPI minimal
- Streaming SSE end-to-end
- Premier exemple fonctionnel

### Phase 2 — Tools & Framework adapters (2 semaines)
- ToolRegistry + agent loop PydanticAI
- `@http_tool` decorator
- Adaptateur Flask
- Adaptateur Django
- Mode librairie pure (async iterator)
- Multi-provider (OpenAI + Gemini)
- Storage SQLite

### Phase 3 — MCP & avancé (2-3 semaines)
- Client MCP côté backend
- UI ConnectorPicker
- OpenAPI import auto
- Auth per-user (ToolContext, OAuth)
- Approval flow tools sensibles
- Rate limiting + caching

### Phase 4 — Polish & Launch (2 semaines)
- Thèmes customisables
- File upload + voice
- Documentation (Docusaurus avec playground)
- Tests E2E (Playwright + pytest)
- Publication npm + PyPI
- CLI `tonpackage-chatbot serve`
- Annonce communauté

---

## 12. Décisions critiques

### CSS de la lib React
**Tailwind avec préfixe `cb-` + scoping `.cb-root`**, pas de `preflight`, un seul `styles.css` à importer. Shadow DOM en V2 si besoin.

### Sécurité des clés API
La clé LLM ne quitte JAMAIS le backend. La lib React connaît seulement l'endpoint + un token applicatif. Non-négociable.

### Streaming Flask
Flask sync par défaut → fournir un helper `async_to_sync_iter()` interne + documenter clairement la config gunicorn (`gevent`/`eventlet` workers) pour la prod. Suggérer Quart pour pure async.

### Persistance
- Client : `localStorage` par défaut
- Serveur : adapter pattern (SQLite, Postgres, Redis)

### Auth per-user
Pas d'auth imposée par la lib. Chaque adaptateur framework expose un `user_context` callable que le dev branche sur son système d'auth existant.

### Versioning protocole
Header `X-Chatbot-Protocol-Version: 1` pour évoluer sans casser.

---

## 13. Risques et mitigations

| Risque | Mitigation |
|--------|------------|
| Conflits CSS sites hôtes | Préfixe Tailwind + scoping + Shadow DOM en option |
| Bundle React trop gros | Tree-shaking, lazy-load shiki, peer deps strictes |
| Streaming Flask en prod | Documenter gunicorn + gevent, suggérer Quart |
| Latence SSE derrière proxies | Documenter nginx/Cloudflare |
| Casser le protocole | Versioning dès le départ |
| MCP encore jeune | Fallback "tools custom only" |
| Multi-framework Python = surface large | Tests d'intégration par adaptateur, exemples maintenus |
| Tools API qui flanchent | Retry/timeout/circuit-breaker built-in |

---

## 14. Concurrence

| Projet | À retenir | À éviter |
|--------|-----------|----------|
| **assistant-ui** | Primitives headless | Couplage providers |
| **Vercel AI SDK** | Protocole streaming | Trop Next.js |
| **CopilotKit** | In-app assistants | Backend opinionated |
| **Chainlit** | Tools Python prêts | Pas une lib embeddable |
| **LibreChat** | Features complètes | Full app, pas une lib |

**Notre angle** : lib React portable + backend Python framework-agnostic + MCP natif + tools API faciles.

---

## 15. Stratégie open-source

- Licence **MIT**
- Monorepo pnpm (`packages/react`, `server/python`, `examples/`, `docs/`)
- CI GitHub Actions (lint, typecheck, tests, build, publish)
- Docs Docusaurus avec playground live
- Discord communautaire
- Annonce HN/Reddit/X quand stable
- Articles techniques sur les choix d'archi

---

## 16. Prochaines étapes immédiates

1. **Valider le protocole** (1 jour) — schémas Pydantic + types TS côte à côte
2. **Setup repo** (0,5 jour) — monorepo, CI, conventions de commit
3. **Spike streaming end-to-end FastAPI + React** (2 jours) — "hello" → réponse Claude streamée
4. **Adaptateur Flask** (1 jour) — valider que le pattern marche aussi en sync
5. **Construire par incréments visibles** à partir de là
