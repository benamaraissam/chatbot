"""Keyword-driven demo scenarios for MockProvider (frontend UI testing)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class MockScenario(StrEnum):
    SIMPLE = "simple"
    THINKING = "thinking"
    WEATHER = "weather"
    FULL = "full"
    APPROVAL = "approval"
    ERROR = "error"
    MARKDOWN = "markdown"
    FUNDS = "funds"


@dataclass(frozen=True)
class ScenarioMatch:
    scenario: MockScenario
    """How many tool-result rounds already exist in the conversation."""
    tool_round: int = 0


def count_tool_rounds(messages: list[Any]) -> int:
    """Count completed tool results in agent message history."""
    role_based = sum(1 for m in messages if getattr(m, "role", None) == "tool")
    if role_based:
        return role_based
    # Legacy plain-text summaries (pre–OpenAI tool messages)
    legacy = 0
    for m in messages:
        content = getattr(m, "content", m if isinstance(m, str) else "")
        if (
            isinstance(content, str)
            and content.startswith("Tool ")
            and (" result:" in content or " error:" in content)
        ):
            legacy += 1
    return legacy


def match_scenario(last_user: str, tool_round: int) -> ScenarioMatch:
    text = last_user.lower().strip()

    if re.search(r"\b(bnp|fund|funds|bnpp|fundsearch)\b", text):
        return ScenarioMatch(MockScenario.FUNDS, tool_round)
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
    {"label": "BNP funds (PV_LU-FSE / ENG)", "message": "search bnp funds PV_LU-FSE ENG"},
]
