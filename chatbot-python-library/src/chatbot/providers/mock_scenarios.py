"""Keyword-driven demo scenarios for MockProvider (frontend UI testing)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class MockScenario(str, Enum):
    SIMPLE = "simple"
    THINKING = "thinking"
    WEATHER = "weather"
    FULL = "full"
    APPROVAL = "approval"
    ERROR = "error"
    MARKDOWN = "markdown"


@dataclass(frozen=True)
class ScenarioMatch:
    scenario: MockScenario
    """How many tool-result rounds already exist in the conversation."""
    tool_round: int = 0


def count_tool_rounds(messages_content: list[str]) -> int:
    """Count completed tool rounds (success or error) in agent message history."""
    return sum(
        1
        for c in messages_content
        if c.startswith("Tool ") and (" result:" in c or " error:" in c)
    )


def match_scenario(last_user: str, tool_round: int) -> ScenarioMatch:
    text = last_user.lower().strip()

    if re.search(r"\b(full|demo|pipeline)\b", text):
        return ScenarioMatch(MockScenario.FULL, tool_round)
    if re.search(r"\b(weather|tool)\b", text):
        return ScenarioMatch(MockScenario.WEATHER, tool_round)
    if re.search(r"\b(think|thinking)\b", text):
        return ScenarioMatch(MockScenario.THINKING, tool_round)
    if re.search(r"\b(approve|approval|email|send)\b", text):
        return ScenarioMatch(MockScenario.APPROVAL, tool_round)
    if re.search(r"\b(error|fail)\b", text):
        return ScenarioMatch(MockScenario.ERROR, tool_round)
    if re.search(r"\b(markdown|code|format)\b", text):
        return ScenarioMatch(MockScenario.MARKDOWN, tool_round)

    return ScenarioMatch(MockScenario.SIMPLE, tool_round)


# Shown in FastAPI root + React demo suggestions
DEMO_HINTS: list[dict[str, str]] = [
    {"label": "Thinking pause", "message": "thinking demo"},
    {"label": "Weather tool", "message": "weather in Tokyo"},
    {"label": "Full pipeline", "message": "full demo"},
    {"label": "Approval gate", "message": "send approval email"},
    {"label": "Tool error", "message": "error demo"},
    {"label": "Markdown", "message": "markdown demo"},
]
