"""PromptRegistry — load and compose system prompts from markdown files.

A *prompt* is a ``.md`` file with YAML frontmatter followed by markdown body
text.  The registry scans a directory, parses every ``.md`` file it finds, and
can compose them into a single system-prompt string.

Typical layout::

    prompts/
        system-prompt.md        # order: 0  — base persona
        finance-addendum.md     # order: 10 — domain instructions

``PromptRegistry.build_system_prompt()`` returns the bodies joined in
``order`` sequence (ties broken alphabetically by name), separated by a blank
line.  This lets you keep a clean base prompt and layer domain-specific
instructions on top without touching the base file.

Example usage in ``bot.py``::

    from chatbot import PromptRegistry

    prompts = PromptRegistry.from_directory(Path(__file__).parent / "prompts")
    system_prompt = prompts.build_system_prompt()
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from chatbot.prompts.frontmatter import PromptFrontmatter

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


@dataclass
class Prompt:
    """A single loaded prompt — frontmatter metadata and markdown body text."""

    frontmatter: PromptFrontmatter
    body: str
    path: Path | None = None

    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.frontmatter.name

    @property
    def order(self) -> int:
        return self.frontmatter.order


class PromptRegistry:
    """Collection of prompts loaded from a directory of ``.md`` files.

    Usage::

        registry = PromptRegistry.from_directory("prompts/")
        system_prompt = registry.build_system_prompt()
    """

    def __init__(self) -> None:
        self._prompts: dict[str, Prompt] = {}

    # ------------------------------------------------------------------ load

    @classmethod
    def from_directory(cls, path: str | Path) -> PromptRegistry:
        """Build a registry by scanning ``path`` for ``.md`` files.

        Silently returns an empty registry if ``path`` does not exist, so
        callers can pass a path unconditionally.
        """
        registry = cls()
        registry.load_directory(path)
        return registry

    def load_directory(self, path: str | Path) -> None:
        """Add every ``.md`` file found directly under ``path`` to this registry.

        Only the top level of ``path`` is scanned (non-recursive) — subdirectories
        are ignored so you can keep assets alongside prompt files freely.
        """
        root = Path(path)
        if not root.exists():
            return
        for md_file in sorted(root.glob("*.md")):
            try:
                self.register(load_prompt_file(md_file))
            except ValueError:
                # Skip files without valid frontmatter (e.g. a plain README.md).
                pass

    def register(self, prompt: Prompt) -> None:
        """Add or replace a prompt in the registry."""
        self._prompts[prompt.name] = prompt

    # ----------------------------------------------------------------- access

    def get(self, name: str) -> Prompt:
        if name not in self._prompts:
            raise KeyError(
                f"Unknown prompt: {name!r}. Available: {sorted(self._prompts.keys())}"
            )
        return self._prompts[name]

    def __contains__(self, name: str) -> bool:
        return name in self._prompts

    def __len__(self) -> int:
        return len(self._prompts)

    def list_prompts(self) -> list[Prompt]:
        """All prompts sorted by (order, name)."""
        return sorted(self._prompts.values(), key=lambda p: (p.order, p.name))

    def names(self) -> list[str]:
        return [p.name for p in self.list_prompts()]

    # --------------------------------------------------------------- compose

    def build_system_prompt(self, *, role: str = "system", sep: str = "\n\n") -> str:
        """Return the composed system prompt string.

        Concatenates the bodies of all prompts whose ``role`` matches (default
        ``"system"``), sorted by ``(order, name)``, joined by ``sep``.

        Returns an empty string if no matching prompts exist.
        """
        parts = [
            p.body.strip()
            for p in self.list_prompts()
            if p.frontmatter.role == role and p.body.strip()
        ]
        return sep.join(parts)


# ---------------------------------------------------------------------------
# File parsing
# ---------------------------------------------------------------------------


def load_prompt_file(path: str | Path) -> Prompt:
    """Parse a single prompt ``.md`` file into a :class:`Prompt`.

    The file must begin with a YAML frontmatter block (``---`` delimited)
    containing at least ``name`` and ``description``.  Files without
    frontmatter raise :exc:`ValueError`.
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")

    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(
            f"{p}: prompt file must start with a YAML frontmatter block "
            "delimited by '---'. "
            "Example: ---\\nname: base\\ndescription: Core persona\\n---\\n"
        )

    raw_frontmatter, body = match.group(1), match.group(2)

    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "Loading prompt files requires PyYAML. Install with: pip install pyyaml"
        ) from exc

    data = yaml.safe_load(raw_frontmatter) or {}
    if not isinstance(data, dict):
        raise ValueError(
            f"{p}: prompt frontmatter must be a YAML mapping, got {type(data).__name__}"
        )

    frontmatter = PromptFrontmatter.from_raw(data)
    return Prompt(frontmatter=frontmatter, body=body, path=p)
