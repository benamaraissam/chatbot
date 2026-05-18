"""Built-in ``load_skill`` tool — auto-registered when skills are provided."""

from __future__ import annotations

from chatbot.core.context import ToolContext
from chatbot.skills.registry import SkillRegistry
from chatbot.tools.registry import ToolRegistry

LOAD_SKILL_TOOL_NAME = "load_skill"


def register_load_skill_tool(tools: ToolRegistry, skills: SkillRegistry) -> None:
    """Register a ``load_skill`` tool that returns a skill's full body on demand.

    Idempotent: skips registration if the tool is already present (e.g. when a
    user overrides it with their own implementation).
    """
    try:
        tools.get(LOAD_SKILL_TOOL_NAME)
        return  # User-defined override exists; respect it.
    except KeyError:
        pass

    async def load_skill(ctx: ToolContext, name: str) -> dict:
        """Load the full instructions for one of the available skills.

        Args:
            name: The exact skill name as shown in the "## Available skills"
                index in the system prompt.

        Returns:
            The skill's full content (instructions, examples, references) so
            you can follow it on the current turn.
        """
        try:
            skill = skills.get(name)
        except KeyError:
            return {
                "error": f"Unknown skill: {name!r}",
                "available": skills.names(),
            }
        return {
            "name": skill.frontmatter.name,
            "description": skill.frontmatter.description,
            "when_to_use": skill.frontmatter.when_to_use,
            "version": skill.frontmatter.version,
            "content": skill.body.strip(),
        }

    tools.register(load_skill, name=LOAD_SKILL_TOOL_NAME)
