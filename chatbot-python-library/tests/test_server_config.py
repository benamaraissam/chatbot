"""Tests for chatbot.server.config — YAML / JSON loader and defaults."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from chatbot.server.config import (
    ProviderSettings,
    ServerConfig,
    load_config,
)


# ─────────────────────────────────────────────────────────────────────────────
# ServerConfig defaults
# ─────────────────────────────────────────────────────────────────────────────

def test_server_config_defaults() -> None:
    cfg = ServerConfig()
    assert cfg.host == "0.0.0.0"
    assert cfg.port == 8000
    assert cfg.default_provider == "mock"
    assert "mock" in cfg.providers
    assert cfg.providers["mock"].model == "mock"
    assert cfg.system_prompt.startswith("You are a helpful")
    assert cfg.storage.startswith("sqlite:")
    assert cfg.cors_origins == ["*"]


def test_provider_settings_supports_env_indirection() -> None:
    p = ProviderSettings(
        model="claude-3-5-sonnet",
        api_key_env="ANTHROPIC_API_KEY",
        base_url_env="ANTHROPIC_BASE_URL",
        extra={"api_version": "2023-06-01"},
    )
    assert p.model == "claude-3-5-sonnet"
    assert p.api_key_env == "ANTHROPIC_API_KEY"
    assert p.extra["api_version"] == "2023-06-01"


# ─────────────────────────────────────────────────────────────────────────────
# load_config
# ─────────────────────────────────────────────────────────────────────────────

def test_load_config_returns_defaults_for_missing_file(tmp_path: Path) -> None:
    # Path does not exist — must return a ServerConfig with defaults.
    cfg = load_config(tmp_path / "missing.yaml")
    assert cfg.port == 8000
    assert "mock" in cfg.providers


def test_load_config_parses_json_when_extension_is_not_yaml(tmp_path: Path) -> None:
    p = tmp_path / "config.json"
    p.write_text(
        json.dumps(
            {
                "port": 9001,
                "default_provider": "openai",
                "providers": {
                    "openai": {"model": "gpt-4o-mini", "api_key_env": "OPENAI_API_KEY"},
                },
                "cors_origins": ["https://app.example.com"],
            }
        ),
        encoding="utf-8",
    )
    cfg = load_config(p)
    assert cfg.port == 9001
    assert cfg.default_provider == "openai"
    assert cfg.providers["openai"].model == "gpt-4o-mini"
    assert cfg.providers["openai"].api_key_env == "OPENAI_API_KEY"
    assert cfg.cors_origins == ["https://app.example.com"]


def test_load_config_parses_yaml_when_extension_is_yaml(tmp_path: Path) -> None:
    try:
        import yaml  # noqa: F401
    except ImportError:
        pytest.skip("pyyaml not installed in this environment")

    p = tmp_path / "config.yaml"
    p.write_text(
        """
host: 127.0.0.1
port: 9002
default_provider: anthropic
providers:
  anthropic:
    model: claude-3-5-sonnet
    api_key_env: ANTHROPIC_API_KEY
system_prompt: |
  You are a fund data assistant.
storage: postgres://user:pw@localhost/db
""".strip(),
        encoding="utf-8",
    )
    cfg = load_config(p)
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 9002
    assert cfg.default_provider == "anthropic"
    assert cfg.providers["anthropic"].model == "claude-3-5-sonnet"
    assert "fund data assistant" in cfg.system_prompt
    assert cfg.storage.startswith("postgres://")


def test_load_config_yaml_empty_file_yields_defaults(tmp_path: Path) -> None:
    try:
        import yaml  # noqa: F401
    except ImportError:
        pytest.skip("pyyaml not installed in this environment")

    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")
    cfg = load_config(p)
    # Empty YAML → load_config falls back to defaults.
    assert cfg.host == "0.0.0.0"
    assert cfg.default_provider == "mock"
