"""Pydantic-validated frontmatter for SKILL.md files.

The schema is intentionally minimal: ``name`` and ``description`` are the only
required fields. Everything else is optional, and any extra YAML keys outside
the known set are preserved in ``metadata`` so projects can grow their own
conventions without breaking existing skills.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# Fields the library knows about. Anything else goes into ``metadata``.
_KNOWN_FIELDS = {
    "name",
    "description",
    "when_to_use",
    "triggers",
    "version",
    "tags",
}


class SkillFrontmatter(BaseModel):
    """Validated metadata block parsed from the top of a ``SKILL.md`` file."""

    name: str = Field(..., description="Stable identifier — used by load_skill(name=...).")
    description: str = Field(
        ...,
        description="One-sentence summary the model sees in the skill index.",
    )
    when_to_use: str | None = Field(
        default=None,
        description="Natural-language guidance shown in the index alongside the description.",
    )
    triggers: list[str] = Field(
        default_factory=list,
        description=(
            "Optional keywords; if any appear (case-insensitive substring) in the "
            "user's latest message, the full skill body is auto-injected into "
            "the system prompt for that turn."
        ),
    )
    version: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Any frontmatter keys outside the known schema, preserved verbatim.",
    )

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "SkillFrontmatter":
        """Construct from a parsed YAML mapping, routing unknown keys into ``metadata``."""
        known = {k: v for k, v in raw.items() if k in _KNOWN_FIELDS}
        extras = {k: v for k, v in raw.items() if k not in _KNOWN_FIELDS and k != "metadata"}
        metadata = dict(extras)
        if isinstance(raw.get("metadata"), dict):
            metadata = {**metadata, **raw["metadata"]}
        known["metadata"] = metadata
        return cls(**known)
