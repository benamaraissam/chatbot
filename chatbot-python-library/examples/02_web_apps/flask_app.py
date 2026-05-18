"""Flask variant of the demo app.

Run from the repo root::

    python examples/02_web_apps/flask_app.py

For production SSE you need an async-capable worker, e.g.::

    gunicorn -k gevent -w 1 -b 0.0.0.0:5000 \\
        --chdir examples/02_web_apps flask_app:app

(Or migrate to Quart if you want fully native async.)

The bot, tools, and provider config are shared with the FastAPI and Django
variants (see ``bot.py`` / ``tools.py`` in this directory).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import Flask, jsonify

from chatbot.env import load_dotenv_file
from chatbot.integrations.flask import create_blueprint
from chatbot.providers.mock_scenarios import DEMO_HINTS

from bot import build_bot, configured_providers  # noqa: E402  — sibling import
from tools import build_tools  # noqa: E402

load_dotenv_file(Path(__file__).resolve().parents[2] / ".env")


# ---------------------------------------------------------------------------
# Framework wiring
# ---------------------------------------------------------------------------

app = Flask(__name__)

tools = build_tools()
bot = build_bot(tools)


def get_user_context() -> dict:
    """Stub auth — replace with flask_login.current_user or your equivalent."""
    return {"user_id": "user_42", "email": "user@example.com"}


bp = create_blueprint(bot, user_context=get_user_context)
app.register_blueprint(bp, url_prefix="/api/chat")


# ---------------------------------------------------------------------------
# Health / discovery
# ---------------------------------------------------------------------------


@app.route("/")
def root():
    return jsonify(
        {
            "framework": "flask",
            "default_provider": bot._default_provider,
            "providers": list(bot.providers.names),
            "configured_providers": configured_providers(),
            "tools": [t.name for t in tools.list_tools()],
            "openai_key_set": bool(os.environ.get("OPENAI_API_KEY")),
            "azure_endpoint_set": bool(os.environ.get("AZURE_OPENAI_ENDPOINT")),
            "anthropic_key_set": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "try_in_chat": [h["message"] for h in DEMO_HINTS],
            "note": "For production SSE use gunicorn -k gevent (see file docstring).",
        }
    )


if __name__ == "__main__":
    # Dev only — switch to gunicorn -k gevent for SSE in production.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
