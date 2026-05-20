"""Tests for prompt frontmatter parsing and PromptRegistry loading + composition."""
from __future__ import annotations

from pathlib import Path

import pytest

from chatbot.prompts.registry import (
    Prompt,
    PromptRegistry,
    load_prompt_file,
)


# ─────────────────────────────────────────────────────────────────────────────
# load_prompt_file
# ─────────────────────────────────────────────────────────────────────────────

def test_load_prompt_file_parses_frontmatter_and_body(tmp_path: Path) -> None:
    md = tmp_path / "base.md"
    md.write_text(
        "---\n"
        "name: base\n"
        "description: Base persona for the assistant.\n"
        "order: 0\n"
        "---\n"
        "You are a helpful assistant.\n",
        encoding="utf-8",
    )

    prompt = load_prompt_file(md)

    assert isinstance(prompt, Prompt)
    assert prompt.name == "base"
    assert prompt.order == 0
    assert prompt.frontmatter.description == "Base persona for the assistant."
    assert prompt.body.strip() == "You are a helpful assistant."
    assert prompt.path == md


def test_load_prompt_file_without_frontmatter_raises(tmp_path: Path) -> None:
    md = tmp_path / "no-frontmatter.md"
    md.write_text("Just a body, no frontmatter.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="frontmatter"):
        load_prompt_file(md)


def test_load_prompt_file_preserves_unknown_keys_in_metadata(tmp_path: Path) -> None:
    md = tmp_path / "custom.md"
    md.write_text(
        "---\n"
        "name: custom\n"
        "description: Has custom keys.\n"
        "owner: trading-desk\n"
        "team: equities\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )

    prompt = load_prompt_file(md)
    # Unknown keys are preserved verbatim in metadata.
    assert prompt.frontmatter.metadata.get("owner") == "trading-desk"
    assert prompt.frontmatter.metadata.get("team") == "equities"


# ─────────────────────────────────────────────────────────────────────────────
# PromptRegistry
# ─────────────────────────────────────────────────────────────────────────────

def _write_prompt(path: Path, name: str, *, order: int = 0, body: str = "Hi.") -> Path:
    path.write_text(
        f"---\nname: {name}\ndescription: desc for {name}\norder: {order}\n---\n{body}\n",
        encoding="utf-8",
    )
    return path


def test_registry_from_directory_loads_all_md_files(tmp_path: Path) -> None:
    _write_prompt(tmp_path / "a.md", "a")
    _write_prompt(tmp_path / "b.md", "b")

    registry = PromptRegistry.from_directory(tmp_path)

    assert len(registry) == 2
    assert set(registry.names()) == {"a", "b"}


def test_registry_skips_files_without_valid_frontmatter(tmp_path: Path) -> None:
    _write_prompt(tmp_path / "valid.md", "valid")
    # A plain README — must not crash the loader.
    (tmp_path / "README.md").write_text("Plain markdown, no frontmatter\n", encoding="utf-8")

    registry = PromptRegistry.from_directory(tmp_path)

    assert "valid" in registry
    assert "README" not in registry
    assert len(registry) == 1


def test_registry_from_directory_returns_empty_on_missing_path(tmp_path: Path) -> None:
    # Should not raise — empty registry is the documented behaviour.
    registry = PromptRegistry.from_directory(tmp_path / "does-not-exist")
    assert len(registry) == 0


def test_registry_register_replaces_existing(tmp_path: Path) -> None:
    p1 = _write_prompt(tmp_path / "x.md", "x", body="first")
    registry = PromptRegistry()
    registry.register(load_prompt_file(p1))

    # Re-register the same name with a different body.
    p2 = _write_prompt(tmp_path / "x2.md", "x", body="second")
    registry.register(load_prompt_file(p2))

    assert len(registry) == 1
    assert registry.get("x").body.strip() == "second"


def test_registry_get_unknown_raises_keyerror_with_available_list(tmp_path: Path) -> None:
    _write_prompt(tmp_path / "alpha.md", "alpha")
    registry = PromptRegistry.from_directory(tmp_path)

    with pytest.raises(KeyError) as exc:
        registry.get("missing")
    # Helpful error: names what's available.
    assert "'alpha'" in str(exc.value)


def test_registry_list_prompts_sorted_by_order_then_name(tmp_path: Path) -> None:
    _write_prompt(tmp_path / "c.md", "c", order=10)
    _write_prompt(tmp_path / "a.md", "a", order=10)
    _write_prompt(tmp_path / "b.md", "b", order=0)

    registry = PromptRegistry.from_directory(tmp_path)
    names = [p.name for p in registry.list_prompts()]

    # order=0 comes first, then alphabetical within order=10.
    assert names == ["b", "a", "c"]


def test_registry_build_system_prompt_joins_bodies_by_order(tmp_path: Path) -> None:
    _write_prompt(tmp_path / "second.md", "second", order=10, body="World.")
    _write_prompt(tmp_path / "first.md", "first", order=0, body="Hello.")

    registry = PromptRegistry.from_directory(tmp_path)
    composed = registry.build_system_prompt()

    # Separator is blank line; first ordered first.
    assert composed == "Hello.\n\nWorld."


def test_registry_build_system_prompt_returns_empty_when_no_matches(tmp_path: Path) -> None:
    # Non-system role is filtered out.
    (tmp_path / "user-msg.md").write_text(
        "---\nname: u\ndescription: d\nrole: user\n---\nA user line.\n",
        encoding="utf-8",
    )
    registry = PromptRegistry.from_directory(tmp_path)

    # Default role filter is 'system', so this returns "".
    assert registry.build_system_prompt() == ""

    # Asking for 'user' returns the body.
    assert registry.build_system_prompt(role="user").strip() == "A user line."
