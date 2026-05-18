"""Django variant of the demo app — single-file ASGI.

Run from the repo root::

    python examples/02_web_apps/django_app.py

This file configures Django in-process via ``settings.configure(...)`` so the
whole project lives in one module — minimal viable Django wiring for a demo.

For a real project you'd put settings, urls, and asgi in separate files and
mount the chatbot router via the snippet shown in ``urls`` below.

The bot, tools, and provider config are shared with the FastAPI and Flask
variants (see ``bot.py`` / ``tools.py`` in this directory).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chatbot.env import load_dotenv_file

load_dotenv_file(Path(__file__).resolve().parents[2] / ".env")


# ---------------------------------------------------------------------------
# Django in-process configuration
# ---------------------------------------------------------------------------

import django  # noqa: E402  — must come AFTER settings.configure is called below
from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        DEBUG=os.environ.get("DJANGO_DEBUG", "1") == "1",
        SECRET_KEY=os.environ.get("DJANGO_SECRET_KEY", "dev-only-not-for-production"),
        ROOT_URLCONF=__name__,           # use the urlpatterns defined below
        ALLOWED_HOSTS=["*"],
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
        ],
        MIDDLEWARE=[],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        USE_TZ=True,
    )
    django.setup()


# ---------------------------------------------------------------------------
# Routes — only safe to import once settings.configure has run
# ---------------------------------------------------------------------------

from django.http import HttpRequest, JsonResponse  # noqa: E402
from django.urls import include, path  # noqa: E402

from chatbot.integrations.django import chatbot_urls  # noqa: E402
from chatbot.providers.mock_scenarios import DEMO_HINTS  # noqa: E402

from bot import build_bot, configured_providers  # noqa: E402
from tools import build_tools  # noqa: E402

tools = build_tools()
bot = build_bot(tools)


def get_user_context(request: HttpRequest) -> dict:
    """Stub auth — replace with ``request.user`` from your auth middleware."""
    return {"user_id": "user_42", "email": "user@example.com"}


def root(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "framework": "django",
            "default_provider": bot._default_provider,
            "providers": list(bot.providers.names),
            "configured_providers": configured_providers(),
            "tools": [t.name for t in tools.list_tools()],
            "openai_key_set": bool(os.environ.get("OPENAI_API_KEY")),
            "azure_endpoint_set": bool(os.environ.get("AZURE_OPENAI_ENDPOINT")),
            "anthropic_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "try_in_chat": [h["message"] for h in DEMO_HINTS],
        }
    )


urlpatterns = [
    path("", root),
    path("api/chat/", include(chatbot_urls(bot, user_context=get_user_context))),
]


# ---------------------------------------------------------------------------
# ASGI application — what uvicorn runs
# ---------------------------------------------------------------------------

from django.core.asgi import get_asgi_application  # noqa: E402

application = get_asgi_application()


if __name__ == "__main__":
    import uvicorn

    # Pass the application object directly so we don't need a module path
    # (this file's module name depends on how it's invoked).
    uvicorn.run(application, host="0.0.0.0", port=int(os.environ.get("PORT", "8001")))
