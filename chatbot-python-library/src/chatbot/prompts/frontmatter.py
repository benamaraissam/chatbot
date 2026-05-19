"""Pydantic-validated frontmatter for prompt markdown files.

Required fields: ``name``, ``description``.
Everything else is optional; unknown keys are preserved in ``metadata``.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

_KNOWN_FIELDS = {"name", "description", "order", "role", "tags", "version"}


class PromptFrontmatter(BaseModel):
    """Validated metadata block parsed from a prompt ``.md`` file."""

    name: str = Field(
        ...,
        description="Stable identifier, e.g. 'base', 'finance-persona'.",
    )
    description: str = Field(
        ...,
        description="One-sentence summary — useful for logging and introspection.",
    )
    order: int = Field(
        default=0,
        description=(
            "Sort key used when composing multiple prompts. Lower values appear "
            "first. Prompts with the same order are sorted by name."
        ),
    )
    role: Literal["system", "user", "assistant"] = Field(
        default="system",
        description=(
            "Which message role this prompt contributes to. "
            "'system' prompts are concatenated into the system prompt. "
            "'user' / 'assistant' prompts are injected as conversation turns "
            "(not yet implemented — reserved for future use)."
        ),
    )
    tags: list[str] = Field(default_factory=list)
    version: str | None = None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Any frontmatter keys outside the known schema, preserved verbatim.",
    )

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> PromptFrontmatter:
        known = {k: v for k, v in raw.items() if k in _KNOWN_FIELDS}
        extras = {k: v for k, v in raw.items() if k not in _KNOWN_FIELDS and k != "metadata"}
        metadata = dict(extras)
        if isinstance(raw.get("metadata"), dict):
            metadata = {**metadata, **raw["metadata"]}
        known["metadata"] = metadata
        return cls(**known)
