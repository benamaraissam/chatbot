"""Tool registry tests."""

import pytest

from chatbot.core.context import ToolContext, UserContext
from chatbot.tools.registry import ToolRegistry


@pytest.fixture
def registry():
    reg = ToolRegistry()

    @reg.register
    async def add(ctx: ToolContext, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    return reg


@pytest.fixture
def ctx():
    return ToolContext(user=UserContext(id="test_user"))


@pytest.mark.asyncio
async def test_tool_register_and_execute(registry, ctx):
    result = await registry.execute("add", {"a": 2, "b": 3}, ctx)
    assert result == 5


@pytest.mark.asyncio
async def test_tool_schema(registry):
    schemas = registry.to_openai_schema()
    assert schemas[0]["name"] == "add"
    assert "a" in schemas[0]["parameters"]["properties"]


@pytest.mark.asyncio
async def test_rate_limit(registry, ctx):
    @registry.register(rate_limit_per_user=2)
    async def limited(ctx: ToolContext) -> str:
        return "ok"

    await registry.execute("limited", {}, ctx)
    await registry.execute("limited", {}, ctx)
    with pytest.raises(RuntimeError, match="Rate limit"):
        await registry.execute("limited", {}, ctx)
