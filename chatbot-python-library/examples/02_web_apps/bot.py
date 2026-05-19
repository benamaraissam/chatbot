"""Shared chatbot factory for the FastAPI, Flask, and Django variants.

Provider selection
------------------
Set ``CHATBOT_DEFAULT_PROVIDER`` to ``mock`` (default), ``openai``, ``azure``,
or ``claude``. Only providers whose credentials are present are registered, so
the server boots with zero config (mock only).

System prompt
-------------
Loaded from the ``prompts/`` directory next to this file via
:class:`~chatbot.PromptRegistry`.  Every ``.md`` file in that directory with
valid YAML frontmatter (``name``, ``description``) contributes to the system
prompt, composed in ``order`` sequence.

To add a domain-specific addendum without touching the base prompt, drop a new
file in ``prompts/`` with a higher ``order`` value::

    # prompts/finance-addendum.md
    ---
    name: finance-addendum
    description: Finance domain guidance
    order: 10
    role: system
    ---
    When the user asks about funds or portfolio data …

Override the prompt directory with ``CHATBOT_PROMPT_DIR``, or bypass the
registry entirely with ``CHATBOT_SYSTEM_PROMPT`` (inline string).

Skills
------
Loaded from the ``skills/`` directory next to this file via
:class:`~chatbot.SkillRegistry`.  Each sub-folder that contains a ``SKILL.md``
becomes a skill the model can call via ``load_skill``.

Override the skills directory with ``CHATBOT_SKILLS_DIR``, or point to a
single ``SKILL.md`` file with ``CHATBOT_SKILL_FILE`` to load just one skill.
"""

from __future__ import annotations

import os
from pathlib import Path

from chatbot import Chatbot, PromptRegistry, SkillRegistry, ToolRegistry

_HERE = Path(__file__).resolve().parent


def _load_system_prompt() -> str:
    """Return the composed system prompt.

    Resolution order:
    1. ``CHATBOT_PROMPT_DIR`` env var — path to a prompts directory.
    2. ``prompts/`` next to this file (default).
    3. ``CHATBOT_SYSTEM_PROMPT`` env var — inline fallback string.
    4. Bare default: ``"You are a helpful assistant."``.
    """
    prompt_dir = os.environ.get("CHATBOT_PROMPT_DIR", "").strip()
    path = Path(prompt_dir) if prompt_dir else _HERE / "prompts"
    if not path.is_absolute():
        path = _HERE / path

    registry = PromptRegistry.from_directory(path)
    if len(registry) > 0:
        return registry.build_system_prompt()

    return os.environ.get("CHATBOT_SYSTEM_PROMPT", "You are a helpful assistant.")


def _build_providers() -> tuple[dict[str, dict], str]:
    """Return (providers dict, default provider name)."""
    providers: dict[str, dict] = {
        "mock": {"model": "mock"},
    }

    if os.environ.get("OPENAI_API_KEY"):
        providers["openai"] = {
            "model": os.environ.get("CHATBOT_OPENAI_MODEL", "gpt-4o"),
            "api_key_env": "OPENAI_API_KEY",
            "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        }

    if os.environ.get("AZURE_OPENAI_ENDPOINT"):
        providers["azure"] = {
            "model": os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            "api_key_env": "AZURE_OPENAI_API_KEY",
            "base_url_env": "AZURE_OPENAI_ENDPOINT",
            "extra": {
                "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            },
        }

    if os.environ.get("ANTHROPIC_API_KEY"):
        providers["claude"] = {
            "model": os.environ.get("CHATBOT_CLAUDE_MODEL", "claude-sonnet-4-20250514"),
            "api_key_env": "ANTHROPIC_API_KEY",
        }

    default = os.environ.get("CHATBOT_DEFAULT_PROVIDER", "mock")
    if default not in providers:
        default = "mock"

    return providers, default


def _load_skills() -> SkillRegistry | None:
    """Return a populated SkillRegistry, or None if no skills are found.

    Resolution order:
    1. ``CHATBOT_SKILL_FILE`` env var — path to a single ``SKILL.md`` file.
    2. ``CHATBOT_SKILLS_DIR`` env var — path to a skills directory.
    3. ``skills/`` next to this file (default).
    """
    skill_file = os.environ.get("CHATBOT_SKILL_FILE", "").strip()
    if skill_file:
        path = Path(skill_file)
        if not path.is_absolute():
            path = _HERE / path
        if not path.exists():
            raise FileNotFoundError(f"CHATBOT_SKILL_FILE not found: {path}")
        return SkillRegistry.from_file(path)

    skills_dir = os.environ.get("CHATBOT_SKILLS_DIR", "").strip()
    path = Path(skills_dir) if skills_dir else _HERE / "skills"
    if not path.is_absolute():
        path = _HERE / path

    registry = SkillRegistry.from_directory(path)
    return registry if len(registry) > 0 else None


def build_bot(tools: ToolRegistry) -> Chatbot:
    """Return a configured Chatbot instance."""
    providers, default = _build_providers()

    skills = _load_skills()

    return Chatbot(
        providers=providers,
        default_provider=default,
        storage=os.environ.get("CHATBOT_STORAGE", "memory"),
        system_prompt=_load_system_prompt(),
        tools=tools,
        max_tool_rounds=int(os.environ.get("CHATBOT_MAX_TOOL_ROUNDS", "10")),
        skills=skills,
    )


def configured_providers() -> list[str]:
    """Names of providers whose credentials are present (used by health routes)."""
    providers, _ = _build_providers()
    return list(providers.keys())
