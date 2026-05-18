"""Chatbot construction shared by the FastAPI, Flask, and Django variants.

The provider stack is built from environment variables so the same code can run
against the mock provider (default), OpenAI, Azure OpenAI, an OpenAI-compatible
gateway (Ollama, vLLM, Moonshot, …), or Anthropic Claude.

Pick the active provider with ``CHATBOT_DEFAULT_PROVIDER`` (``mock`` | ``openai``
| ``azure`` | ``claude``). Only providers whose endpoint or key is set get
registered, so the example still boots end-to-end with zero config.
"""

from __future__ import annotations

import os
from pathlib import Path

from chatbot import Chatbot, SkillRegistry, ToolRegistry


def build_bot(tools: ToolRegistry) -> Chatbot:
    """Return a Chatbot wired to every provider whose credentials are present."""
    providers: dict[str, dict] = {
        # The mock provider is always available — drives the React demo UI
        # scenarios (``thinking demo``, ``weather``, etc.).
        "mock": {"model": "mock"},
    }

    # --- OpenAI / OpenAI-compatible gateways (Ollama, vLLM, Moonshot, …) ----
    if os.environ.get("OPENAI_API_KEY"):
        providers["openai"] = {
            "model": os.environ.get("CHATBOT_OPENAI_MODEL", "gpt-4o"),
            "api_key_env": "OPENAI_API_KEY",
            "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        }

    # --- Azure OpenAI ------------------------------------------------------
    if os.environ.get("AZURE_OPENAI_ENDPOINT"):
        providers["azure"] = {
            "model": os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            "api_key_env": "AZURE_OPENAI_API_KEY",
            "base_url_env": "AZURE_OPENAI_ENDPOINT",
            "extra": {
                "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            },
        }

    # --- Anthropic Claude --------------------------------------------------
    if os.environ.get("ANTHROPIC_API_KEY"):
        providers["claude"] = {
            "model": os.environ.get("CHATBOT_CLAUDE_MODEL", "claude-sonnet-4-20250514"),
            "api_key_env": "ANTHROPIC_API_KEY",
        }

    default = os.environ.get("CHATBOT_DEFAULT_PROVIDER", "mock")
    if default not in providers:
        # Fall back to mock if the requested provider isn't configured.
        default = "mock"

    # Load SKILL.md files from ./skills/ if the directory exists. Silently
    # no-ops otherwise, so the example still boots when skills are removed.
    skills_dir = Path(__file__).parent / "skills"
    skills = SkillRegistry.from_directory(skills_dir)

    return Chatbot(
        providers=providers,
        default_provider=default,
        storage=os.environ.get("CHATBOT_STORAGE", "memory"),
        system_prompt=os.environ.get(
            "CHATBOT_SYSTEM_PROMPT",
            "You are a helpful assistant. When you need data, prefer calling "
            "tools over guessing. Cite the tool name in your reasoning.",
        ),
        tools=tools,
        max_tool_rounds=int(os.environ.get("CHATBOT_MAX_TOOL_ROUNDS", "10")),
        skills=skills if len(skills) else None,
    )


def configured_providers() -> list[str]:
    """Tiny introspection helper used by the framework variants' health route."""
    names = ["mock"]
    if os.environ.get("OPENAI_API_KEY"):
        names.append("openai")
    if os.environ.get("AZURE_OPENAI_ENDPOINT"):
        names.append("azure")
    if os.environ.get("ANTHROPIC_API_KEY"):
        names.append("claude")
    return names
