"""Standalone server configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import json

from pydantic import BaseModel, Field


class ProviderSettings(BaseModel):
    model: str
    api_key: str | None = None
    api_key_env: str | None = None
    base_url: str | None = None
    base_url_env: str | None = None


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    default_provider: str = "mock"
    providers: dict[str, ProviderSettings] = Field(
        default_factory=lambda: {"mock": ProviderSettings(model="mock")}
    )
    system_prompt: str = "You are a helpful assistant."
    storage: str = "sqlite:///./chatbot.db"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


def load_config(path: str | Path) -> ServerConfig:
    path = Path(path)
    if not path.exists():
        return ServerConfig()
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as exc:
            raise ImportError("Install pyyaml for YAML config: pip install pyyaml") from exc
        raw: dict[str, Any] = yaml.safe_load(text) or {}
    else:
        raw = json.loads(text)
    return ServerConfig.model_validate(raw)
