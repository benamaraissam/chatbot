"""Mock provider for tests and offline demos — simulates thinking, tools, approval, errors."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from chatbot.protocol.multimodal import provider_content_to_text
from chatbot.providers.base import (
    BaseProvider,
    ProviderConfig,
    ProviderMessage,
    ProviderStreamChunk,
)
from chatbot.providers.mock_scenarios import (
    MockScenario,
    ScenarioMatch,
    count_tool_rounds,
    match_scenario,
)

# Delays (seconds) — tuned for visible UI feedback without feeling sluggish
TOOL_GAP = 0.25
CHAR_DELAY = 0.012
WORD_DELAY = 0.028
THINKING_CHAR_DELAY = 0.016

DEFAULT_THINKING = (
    "Let me work through this carefully.\n\n"
    "First, I'll interpret what you're asking and what data I need. "
    "Then I'll decide whether to call a tool or answer directly. "
    "I'll keep the reasoning concise and focused on the next step."
)


class MockProvider(BaseProvider):
    name = "mock"

    def __init__(self, config: ProviderConfig | None = None) -> None:
        super().__init__(config or ProviderConfig(model="mock"))

    def pydantic_ai_model(self) -> str:
        return "test"

    async def _stream_thinking(
        self,
        text: str | None = None,
        *,
        delay: float = THINKING_CHAR_DELAY,
    ) -> AsyncIterator[ProviderStreamChunk]:
        content = text or DEFAULT_THINKING
        for ch in content:
            await asyncio.sleep(delay)
            yield ProviderStreamChunk(thinking_delta=ch)

    async def _stream_chars(
        self, text: str, *, delay: float = CHAR_DELAY
    ) -> AsyncIterator[ProviderStreamChunk]:
        for ch in text:
            await asyncio.sleep(delay)
            yield ProviderStreamChunk(text_delta=ch)

    async def _stream_words(self, text: str) -> AsyncIterator[ProviderStreamChunk]:
        for word in text.split():
            await asyncio.sleep(WORD_DELAY)
            yield ProviderStreamChunk(text_delta=word + " ")

    async def _run_image_ack(self) -> AsyncIterator[ProviderStreamChunk]:
        """Short reply when the user message includes an image attachment."""
        reply = (
            "I received your image. In production this is sent to a vision-capable model "
            "(e.g. Kimi with `CHATBOT_DEFAULT_PROVIDER=openai`). "
            "Describe what you see or ask a specific question about the image."
        )
        async for chunk in self._stream_words(reply):
            yield chunk
        yield ProviderStreamChunk(
            finish_reason="stop",
            usage={"prompt_tokens": 120, "completion_tokens": 40, "total_tokens": 160},
        )

    async def _stream_tool(
        self,
        *,
        tool_id: str,
        name: str,
        input_data: dict[str, Any],
        stream_input: bool = True,
    ) -> AsyncIterator[ProviderStreamChunk]:
        yield ProviderStreamChunk(tool_name=name, tool_call_id=tool_id, tool_input={})
        await asyncio.sleep(TOOL_GAP)

        if stream_input:
            raw = json.dumps(input_data, separators=(",", ":"))
            for ch in raw:
                await asyncio.sleep(CHAR_DELAY)
                yield ProviderStreamChunk(tool_input_delta=ch, tool_call_id=tool_id)

        yield ProviderStreamChunk(
            finish_reason="tool_calls",
            usage={"prompt_tokens": 14, "completion_tokens": 10, "total_tokens": 24},
        )

    async def _finish_text(self) -> ProviderStreamChunk:
        return ProviderStreamChunk(
            finish_reason="stop",
            usage={"prompt_tokens": 20, "completion_tokens": 40, "total_tokens": 60},
        )

    async def _run_simple(self, last_user: str) -> AsyncIterator[ProviderStreamChunk]:
        reply = (
            f"Hi! You said: **{last_user}**. "
            "Try `full demo`, `weather`, `thinking`, or `send approval email`."
        )
        async for chunk in self._stream_words(reply):
            yield chunk
        yield await self._finish_text()

    async def _run_thinking(self, last_user: str) -> AsyncIterator[ProviderStreamChunk]:
        reasoning = (
            f"The user asked: \"{last_user}\"\n\n"
            "I should clarify the intent, check if tools are required, "
            "and only then produce a direct answer without unnecessary steps."
        )
        async for chunk in self._stream_thinking(reasoning, delay=0.02):
            yield chunk
        await asyncio.sleep(0.35)
        reply = (
            "After reasoning through your question, here's my answer. "
            f'You asked about: "{last_user}". '
            "In production, the thinking block above is streamed via `thinking_delta` events."
        )
        async for chunk in self._stream_words(reply):
            yield chunk
        yield await self._finish_text()

    async def _run_weather(self, tool_round: int) -> AsyncIterator[ProviderStreamChunk]:
        if tool_round > 0:
            summary = (
                "Here's the forecast from **get_weather**: Tokyo is **18°C** and sunny "
                "(humidity 42%). Great day to be outside."
            )
            async for chunk in self._stream_words(summary):
                yield chunk
            yield await self._finish_text()
            return

        async for chunk in self._stream_thinking(
            "I need live weather data. I'll call get_weather with the city from the user's message."
        ):
            yield chunk
        async for chunk in self._stream_tool(
            tool_id="tool_weather_1",
            name="get_weather",
            input_data={"city": "Tokyo"},
        ):
            yield chunk

    async def _run_full(self, tool_round: int) -> AsyncIterator[ProviderStreamChunk]:
        if tool_round == 0:
            async for chunk in self._stream_thinking(
                "Step 1: fetch weather for Paris, then search docs for related events."
            ):
                yield chunk
            async for chunk in self._stream_tool(
                tool_id="tool_weather_1",
                name="get_weather",
                input_data={"city": "Paris"},
            ):
                yield chunk
            return

        if tool_round == 1:
            async for chunk in self._stream_thinking(
                "Weather received. Now searching the knowledge base for weekend events."
            ):
                yield chunk
            async for chunk in self._stream_tool(
                tool_id="tool_search_1",
                name="search_docs",
                input_data={"query": "weekend events", "limit": 3},
            ):
                yield chunk
            return

        async for chunk in self._stream_thinking(
            "Both tools succeeded. I'll synthesize a short summary for the user."
        ):
            yield chunk
        final = (
            "Here's your **full demo** summary:\n\n"
            "1. **get_weather** → Paris is 18°C and sunny.\n"
            "2. **search_docs** → Found 3 relevant articles.\n\n"
            "Everything streamed over SSE with tool cards inline in the UI."
        )
        async for chunk in self._stream_words(final):
            yield chunk
        yield await self._finish_text()

    async def _run_approval(self, tool_round: int) -> AsyncIterator[ProviderStreamChunk]:
        if tool_round > 0:
            reply = (
                "Email **sent** after your approval. "
                "The agent resumed with `approvedToolIds` in metadata."
            )
            async for chunk in self._stream_words(reply):
                yield chunk
            yield await self._finish_text()
            return

        async for chunk in self._stream_thinking(
            "This action sends an email. It requires explicit user approval before execution."
        ):
            yield chunk
        async for chunk in self._stream_tool(
            tool_id="tool_email_1",
            name="send_email",
            input_data={
                "to": "user@example.com",
                "subject": "Trip confirmation",
                "body": "Your booking is confirmed.",
            },
        ):
            yield chunk

    async def _run_error(self, tool_round: int) -> AsyncIterator[ProviderStreamChunk]:
        if tool_round > 0:
            reply = (
                "The tool failed as expected. The UI should show a **Failed** tool card "
                "with the error output, then this follow-up message."
            )
            async for chunk in self._stream_words(reply):
                yield chunk
            yield await self._finish_text()
            return

        async for chunk in self._stream_thinking(
            "I'll call a tool that is expected to fail so we can test error UI states."
        ):
            yield chunk
        async for chunk in self._stream_tool(
            tool_id="tool_fail_1",
            name="simulate_failure",
            input_data={"reason": "upstream timeout"},
        ):
            yield chunk

    async def _run_funds(self, tool_round: int) -> AsyncIterator[ProviderStreamChunk]:
        if tool_round > 0:
            summary = (
                "Got the BNP Paribas AM fund list back from **bnpp_fund_search** "
                "(profile `PV_LU-FSE`, language `ENG`). The tool card above shows the raw "
                "JSON response from the live API."
            )
            async for chunk in self._stream_words(summary):
                yield chunk
            yield await self._finish_text()
            return

        async for chunk in self._stream_thinking(
            "I'll call bnpp_fund_search with profile=PV_LU-FSE and language=ENG "
            "to hit the BNP Paribas AM fund-search API."
        ):
            yield chunk
        async for chunk in self._stream_tool(
            tool_id="tool_bnpp_funds_1",
            name="bnpp_fund_search",
            input_data={
                "profile": "PV_LU-FSE",
                "language": "ENG",
                "limit": 10,
                "offset": 0,
            },
        ):
            yield chunk

    async def _run_markdown(self) -> AsyncIterator[ProviderStreamChunk]:
        async for chunk in self._stream_thinking(
            "I'll format the response with markdown: table, code block, and list."
        ):
            yield chunk
        body = (
            "Markdown demo:\n\n"
            "| Step | Status |\n"
            "|------|--------|\n"
            "| Stream | OK |\n"
            "| Tools | OK |\n\n"
            "```python\n"
            "async def hello():\n"
            "    return 'world'\n"
            "```\n\n"
            "- Bullet one\n"
            "- Bullet two\n"
        )
        async for chunk in self._stream_chars(body, delay=0.008):
            yield chunk
        yield await self._finish_text()

    async def _dispatch(
        self, match: ScenarioMatch, last_user: str
    ) -> AsyncIterator[ProviderStreamChunk]:
        scenario = match.scenario
        tool_round = match.tool_round

        if scenario == MockScenario.SIMPLE:
            async for c in self._run_simple(last_user):
                yield c
        elif scenario == MockScenario.THINKING:
            async for c in self._run_thinking(last_user):
                yield c
        elif scenario == MockScenario.WEATHER:
            async for c in self._run_weather(tool_round):
                yield c
        elif scenario == MockScenario.FULL:
            async for c in self._run_full(tool_round):
                yield c
        elif scenario == MockScenario.APPROVAL:
            async for c in self._run_approval(tool_round):
                yield c
        elif scenario == MockScenario.ERROR:
            async for c in self._run_error(tool_round):
                yield c
        elif scenario == MockScenario.MARKDOWN:
            async for c in self._run_markdown():
                yield c
        elif scenario == MockScenario.FUNDS:
            async for c in self._run_funds(tool_round):
                yield c

    async def stream(
        self,
        messages: list[ProviderMessage],
        *,
        system_prompt: str | None = None,
        tools_schema: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> AsyncIterator[ProviderStreamChunk]:
        last_user = next(
            (provider_content_to_text(m.content) for m in reversed(messages) if m.role == "user"),
            "",
        )
        tool_round = count_tool_rounds(messages)

        # After tool execution the agent appends synthetic user messages —
        # keep scenario from first user ask
        first_user = next(
            (provider_content_to_text(m.content) for m in messages if m.role == "user"),
            last_user,
        )
        if "[Image]" in last_user and tool_round == 0:
            async for chunk in self._run_image_ack():
                yield chunk
            return
        match = match_scenario(first_user, tool_round)

        async for chunk in self._dispatch(match, last_user):
            yield chunk
