"""Tests for chatbot.skills — frontmatter, registry, trigger matching, and Chatbot wiring."""

from __future__ import annotations

import textwrap

import pytest

from chatbot import Chatbot, Skill, SkillFrontmatter, SkillRegistry
from chatbot.core.context import ToolContext, UserContext
from chatbot.skills.load_tool import LOAD_SKILL_TOOL_NAME, register_load_skill_tool
from chatbot.skills.registry import load_skill_file
from chatbot.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_skill(tmp_path, name: str, frontmatter: str, body: str = "Body text") -> None:
    skill_dir = tmp_path / name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n{body}\n", encoding="utf-8")


@pytest.fixture
def ctx():
    return ToolContext(user=UserContext(id="u1"))


# ---------------------------------------------------------------------------
# SkillFrontmatter
# ---------------------------------------------------------------------------


def test_frontmatter_required_fields_only():
    fm = SkillFrontmatter.from_raw({"name": "x", "description": "y"})
    assert fm.name == "x"
    assert fm.description == "y"
    assert fm.triggers == []
    assert fm.tags == []
    assert fm.metadata == {}


def test_frontmatter_routes_unknown_keys_into_metadata():
    fm = SkillFrontmatter.from_raw(
        {
            "name": "x",
            "description": "y",
            "triggers": ["foo"],
            "owner": "team-platform",  # unknown — goes to metadata
            "internal_id": 42,         # unknown — goes to metadata
        }
    )
    assert fm.triggers == ["foo"]
    assert fm.metadata == {"owner": "team-platform", "internal_id": 42}


def test_frontmatter_explicit_metadata_key_is_preserved():
    fm = SkillFrontmatter.from_raw(
        {
            "name": "x",
            "description": "y",
            "metadata": {"k": "v"},
            "extra_key": "also goes to metadata",
        }
    )
    # Both the explicit metadata.k AND the unknown extra_key end up in metadata.
    assert fm.metadata == {"k": "v", "extra_key": "also goes to metadata"}


def test_frontmatter_rejects_missing_required():
    with pytest.raises(Exception):
        SkillFrontmatter.from_raw({"description": "missing name"})


# ---------------------------------------------------------------------------
# load_skill_file + SkillRegistry.from_directory
# ---------------------------------------------------------------------------


def test_load_skill_file_parses_frontmatter_and_body(tmp_path):
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(
        textwrap.dedent(
            """\
            ---
            name: invoice
            description: Process invoices.
            when_to_use: When the user mentions an invoice.
            triggers: [invoice, facture]
            ---
            # Invoice processing

            ## Steps
            1. Read.
            2. Validate.
            """
        ),
        encoding="utf-8",
    )

    skill = load_skill_file(skill_md)
    assert skill.frontmatter.name == "invoice"
    assert skill.frontmatter.triggers == ["invoice", "facture"]
    assert "# Invoice processing" in skill.body
    assert skill.path == tmp_path


def test_load_skill_file_requires_frontmatter(tmp_path):
    bad = tmp_path / "SKILL.md"
    bad.write_text("no frontmatter here", encoding="utf-8")
    with pytest.raises(ValueError, match="frontmatter"):
        load_skill_file(bad)


def test_registry_from_directory_finds_all_skill_md(tmp_path):
    _write_skill(tmp_path, "alpha", "name: alpha\ndescription: A")
    _write_skill(tmp_path, "beta", "name: beta\ndescription: B")
    (tmp_path / "noise.md").write_text("not a skill", encoding="utf-8")

    reg = SkillRegistry.from_directory(tmp_path)
    assert set(reg.names()) == {"alpha", "beta"}


def test_registry_from_missing_directory_is_silent(tmp_path):
    reg = SkillRegistry.from_directory(tmp_path / "does_not_exist")
    assert len(reg) == 0


# ---------------------------------------------------------------------------
# System prompt + trigger matching
# ---------------------------------------------------------------------------


def test_build_index_addendum_lists_every_skill(tmp_path):
    _write_skill(tmp_path, "a", "name: a\ndescription: A summary\nwhen_to_use: when A")
    _write_skill(tmp_path, "b", "name: b\ndescription: B summary")
    reg = SkillRegistry.from_directory(tmp_path)
    text = reg.build_index_addendum()
    assert "## Available skills" in text
    assert "**a** — A summary" in text
    assert "*When to use:* when A" in text
    assert "**b** — B summary" in text


def test_build_index_addendum_empty_when_no_skills():
    assert SkillRegistry().build_index_addendum() == ""


def test_match_triggers_case_insensitive(tmp_path):
    _write_skill(tmp_path, "funds", "name: funds\ndescription: F\ntriggers: [Fund, ISIN]")
    reg = SkillRegistry.from_directory(tmp_path)
    assert [s.name for s in reg.match_triggers("Show me FUND list")] == ["funds"]
    assert [s.name for s in reg.match_triggers("what's the ISIN for X?")] == ["funds"]
    assert reg.match_triggers("unrelated query") == []


def test_match_triggers_skill_with_no_triggers_never_matches(tmp_path):
    _write_skill(tmp_path, "x", "name: x\ndescription: X")  # no triggers
    reg = SkillRegistry.from_directory(tmp_path)
    assert reg.match_triggers("anything") == []


def test_build_trigger_addendum_emits_full_bodies(tmp_path):
    _write_skill(
        tmp_path, "x", "name: x\ndescription: X", body="Detailed instructions for X."
    )
    reg = SkillRegistry.from_directory(tmp_path)
    skills = reg.list_skills()
    out = reg.build_trigger_addendum(skills)
    assert "## Skill auto-loaded: x" in out
    assert "Detailed instructions for X." in out


# ---------------------------------------------------------------------------
# load_skill built-in tool
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_load_skill_tool_executes(tmp_path, ctx):
    _write_skill(tmp_path, "alpha", "name: alpha\ndescription: A", body="Alpha body.")
    reg = SkillRegistry.from_directory(tmp_path)

    tools = ToolRegistry()
    register_load_skill_tool(tools, reg)

    assert LOAD_SKILL_TOOL_NAME in [t.name for t in tools.list_tools()]
    result = await tools.execute(LOAD_SKILL_TOOL_NAME, {"name": "alpha"}, ctx)
    assert result["name"] == "alpha"
    assert "Alpha body." in result["content"]


@pytest.mark.asyncio
async def test_load_skill_tool_handles_unknown_name(tmp_path, ctx):
    _write_skill(tmp_path, "alpha", "name: alpha\ndescription: A")
    reg = SkillRegistry.from_directory(tmp_path)

    tools = ToolRegistry()
    register_load_skill_tool(tools, reg)
    result = await tools.execute(LOAD_SKILL_TOOL_NAME, {"name": "missing"}, ctx)
    assert "error" in result
    assert "alpha" in result["available"]


def test_register_load_skill_tool_respects_existing_override(tmp_path):
    reg = SkillRegistry()
    tools = ToolRegistry()

    @tools.register
    async def load_skill(ctx, name: str) -> dict:
        """Custom load_skill — must NOT be overwritten by register_load_skill_tool."""
        return {"custom": True, "name": name}

    register_load_skill_tool(tools, reg)
    # Still the user's override.
    same = tools.get(LOAD_SKILL_TOOL_NAME)
    assert same.fn.__doc__.startswith("Custom")


# ---------------------------------------------------------------------------
# Chatbot integration
# ---------------------------------------------------------------------------


def _make_skills(tmp_path) -> SkillRegistry:
    _write_skill(
        tmp_path,
        "funds",
        "name: funds\ndescription: Fund queries.\ntriggers: [fund, isin]",
        body="Body of the funds skill.",
    )
    return SkillRegistry.from_directory(tmp_path)


@pytest.mark.asyncio
async def test_chatbot_appends_skill_index_to_system_prompt(tmp_path):
    skills = _make_skills(tmp_path)
    bot = Chatbot(default_provider="mock", storage="memory", skills=skills)

    assert "## Available skills" in bot.system_prompt
    assert "**funds** — Fund queries." in bot.system_prompt


@pytest.mark.asyncio
async def test_chatbot_auto_registers_load_skill_tool(tmp_path):
    skills = _make_skills(tmp_path)
    bot = Chatbot(default_provider="mock", storage="memory", skills=skills)
    assert LOAD_SKILL_TOOL_NAME in [t.name for t in bot.tools.list_tools()]


@pytest.mark.asyncio
async def test_chatbot_effective_prompt_injects_triggered_skill_body(tmp_path):
    skills = _make_skills(tmp_path)
    bot = Chatbot(default_provider="mock", storage="memory", skills=skills)

    matched_prompt = bot._effective_system_prompt("I want to see a FUND list")
    assert "Body of the funds skill." in matched_prompt
    assert "## Skill auto-loaded: funds" in matched_prompt


@pytest.mark.asyncio
async def test_chatbot_effective_prompt_no_op_when_no_trigger_match(tmp_path):
    skills = _make_skills(tmp_path)
    bot = Chatbot(default_provider="mock", storage="memory", skills=skills)
    same = bot._effective_system_prompt("totally unrelated query about weather")
    assert "## Skill auto-loaded" not in same
    assert same == bot.system_prompt


@pytest.mark.asyncio
async def test_chatbot_without_skills_is_unaffected():
    bot = Chatbot(default_provider="mock", storage="memory")
    assert "## Available skills" not in bot.system_prompt
    assert LOAD_SKILL_TOOL_NAME not in [t.name for t in bot.tools.list_tools()]
    # _effective_system_prompt should be a clean no-op
    assert bot._effective_system_prompt("anything") == bot.system_prompt
