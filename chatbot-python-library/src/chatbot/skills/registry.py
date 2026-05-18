"""Skill + SkillRegistry — load SKILL.md files, surface them to the agent.

A *skill* is a folder containing a ``SKILL.md`` file with Pydantic-validated
YAML frontmatter and a markdown body. Skills are surfaced to the model in three
ways simultaneously:

1. **System prompt index** — every skill's ``name`` + ``description`` (+ optional
   ``when_to_use``) is appended to the system prompt so the model knows what
   exists. Zero context cost for skill bodies that aren't loaded.
2. **Built-in ``load_skill`` tool** — the model can pull the full body of any
   skill on demand. Auto-registered when a ``SkillRegistry`` is passed to
   ``Chatbot(skills=...)``.
3. **Trigger keywords** — if ``triggers`` is set on a skill and a matching
   keyword appears in the user's latest message (case-insensitive substring),
   the full body is auto-injected into that turn's system prompt — no tool
   round-trip required.

Skills are not a replacement for tools or MCP — they're prose for the model to
read. Tool docstrings tell the model *what a tool does*; skills tell it
*how to combine tools to accomplish a task*.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from chatbot.skills.frontmatter import SkillFrontmatter

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


@dataclass
class Skill:
    """A single loaded skill — frontmatter, body, and source path."""

    frontmatter: SkillFrontmatter
    body: str
    path: Path | None = None
    """Directory holding ``SKILL.md`` (None for skills created programmatically).
    Resources referenced by the skill body live relative to this path."""

    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.frontmatter.name


class SkillRegistry:
    """Collection of skills, with directory-scan loading and matching helpers."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    # ------------------------------------------------------------------ load

    @classmethod
    def from_directory(cls, path: str | Path) -> SkillRegistry:
        """Build a registry by recursively scanning ``path`` for ``SKILL.md`` files."""
        registry = cls()
        registry.load_directory(path)
        return registry

    def load_directory(self, path: str | Path) -> None:
        """Add every SKILL.md found under ``path`` to this registry.

        Silently no-ops if ``path`` does not exist, so apps can call this
        unconditionally (e.g. ``./skills`` may not be present on every deploy).
        """
        root = Path(path)
        if not root.exists():
            return
        for skill_md in sorted(root.rglob("SKILL.md")):
            self.register(load_skill_file(skill_md))

    def register(self, skill: Skill) -> None:
        self._skills[skill.frontmatter.name] = skill

    # ------------------------------------------------------------- access

    def get(self, name: str) -> Skill:
        if name not in self._skills:
            raise KeyError(
                f"Unknown skill: {name!r}. Available: {sorted(self._skills.keys())}"
            )
        return self._skills[name]

    def __contains__(self, name: str) -> bool:
        return name in self._skills

    def __len__(self) -> int:
        return len(self._skills)

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def names(self) -> list[str]:
        return sorted(self._skills.keys())

    # ---------------------------------------------------------- exposure

    def build_index_addendum(self) -> str:
        """Compact "## Available skills" block to append to the system prompt.

        Lists name + description (+ when_to_use if set) for every skill. Skill
        bodies are NOT included here — the model pulls them via ``load_skill``
        or via trigger auto-injection.
        """
        if not self._skills:
            return ""
        lines = [
            "## Available skills",
            "",
            "You have access to the skills listed below. Each gives instructions, "
            "examples, and references for a specific kind of task. When a skill "
            "looks relevant to the user's request, call the `load_skill` tool with "
            "the skill's `name` to read its full content before acting.",
            "",
        ]
        for skill in self._skills.values():
            f = skill.frontmatter
            lines.append(f"- **{f.name}** — {f.description}")
            if f.when_to_use:
                lines.append(f"  *When to use:* {f.when_to_use}")
        return "\n".join(lines)

    def match_triggers(self, user_text: str) -> list[Skill]:
        """Return skills whose triggers match ``user_text`` (case-insensitive substring).

        A skill with no triggers never matches via this path — the model must
        discover it via the index + ``load_skill``.
        """
        if not user_text or not self._skills:
            return []
        haystack = user_text.lower()
        hits: list[Skill] = []
        for skill in self._skills.values():
            for trigger in skill.frontmatter.triggers:
                if trigger.strip() and trigger.lower() in haystack:
                    hits.append(skill)
                    break
        return hits

    def build_trigger_addendum(self, skills: list[Skill]) -> str:
        """Render the full bodies of triggered skills for injection into the prompt."""
        if not skills:
            return ""
        sections = []
        for skill in skills:
            sections.append(
                f"## Skill auto-loaded: {skill.frontmatter.name}\n\n{skill.body.strip()}"
            )
        return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# SKILL.md parsing
# ---------------------------------------------------------------------------


def load_skill_file(path: str | Path) -> Skill:
    """Parse a single ``SKILL.md`` file into a :class:`Skill`."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")

    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(
            f"{p}: SKILL.md must start with a YAML frontmatter block delimited by '---'. "
            "Example: ---\\nname: my_skill\\ndescription: ...\\n---\\n"
        )

    raw_frontmatter, body = match.group(1), match.group(2)

    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "Loading SKILL.md files requires PyYAML. Install with: pip install pyyaml"
        ) from exc

    data = yaml.safe_load(raw_frontmatter) or {}
    if not isinstance(data, dict):
        raise ValueError(
            f"{p}: SKILL.md frontmatter must be a YAML mapping, got {type(data).__name__}"
        )

    frontmatter = SkillFrontmatter.from_raw(data)
    return Skill(frontmatter=frontmatter, body=body, path=p.parent)
