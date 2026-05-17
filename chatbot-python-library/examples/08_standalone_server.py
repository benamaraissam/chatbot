"""Example 08 — Standalone server via CLI or programmatic app."""

from chatbot.server.app import create_app
from chatbot.server.config import ServerConfig

# Option A: programmatic
config = ServerConfig(
    host="0.0.0.0",
    port=8000,
    default_provider="mock",
    storage="sqlite:///./chatbot.db",
)
app = create_app(config)

# Option B: CLI
#   chatbot serve --config config.yaml --port 8000

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.host, port=config.port)
