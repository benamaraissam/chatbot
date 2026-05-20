---
name: write-tests
description: Use when adding a new test (or filling in coverage) for the chatbot Python library. Triggers include "write a test for", "add coverage for", "regression test", "test that ...", or any request implying creation of a new pytest test in this repo.
---

# Writing tests for the chatbot Python library

Tests live under `tests/` and mirror the package layout under `src/chatbot/`.
`pytest-asyncio` is in **auto mode** (configured in `pyproject.toml`), so
async tests do not need an explicit decorator.

## File placement

| Code under test | Test file |
|---|---|
| `src/chatbot/core/...` | `tests/test_chatbot.py`, `tests/test_agent_multi_tool.py`, `tests/test_max_tool_rounds.py` |
| `src/chatbot/providers/openai.py` | `tests/test_openai_stream.py`, `tests/test_openai_messages.py` |
| `src/chatbot/providers/azure_openai.py` | `tests/test_azure_openai.py` |
| `src/chatbot/providers/mock_scenarios.py` | `tests/test_mock_scenarios.py` |
| `src/chatbot/tools/...` | `tests/test_tools.py`, `tests/test_pagination.py` |
| `src/chatbot/storage/...` | `tests/test_storage.py` |
| `src/chatbot/protocol/...` | `tests/test_protocol.py`, `tests/test_multimodal.py` |
| `src/chatbot/skills/...` | `tests/test_skills.py` |
| `src/chatbot/integrations/fastapi.py` | `tests/test_fastapi.py` |

If no existing module fits, create a new `tests/test_<area>.py` file rather
than dumping unrelated tests into an existing one.

## Canonical patterns

### 1. Async test against the agent loop (uses the mock provider)

```python
from chatbot.core.chatbot import Chatbot
from chatbot.providers.mock import MockProvider

async def test_single_turn_completes():
    bot = Chatbot(provider=MockProvider.reply("hello"))
    reply = await bot.send("hi")
    assert reply.text == "hello"
```

### 2. Multi-turn with scripted scenarios

```python
from chatbot.providers.mock_scenarios import scripted_provider

async def test_two_turns():
    provider = scripted_provider([
        {"text": "first"},
        {"text": "second"},
    ])
    bot = Chatbot(provider=provider)
    assert (await bot.send("a")).text == "first"
    assert (await bot.send("b")).text == "second"
```

### 3. Tool registration & invocation

```python
from chatbot.tools.registry import ToolRegistry

def test_register_python_callable():
    reg = ToolRegistry()

    @reg.tool
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    spec = reg.get_spec("add")
    assert spec.input_schema["properties"].keys() == {"a", "b"}
```

### 4. FastAPI integration (uses `httpx.AsyncClient`, never uvicorn)

```python
import httpx
from fastapi import FastAPI
from chatbot.integrations.fastapi import mount

async def test_chat_endpoint_streams(agent_fixture):
    app = FastAPI()
    mount(app, agent=agent_fixture)
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        async with client.stream("POST", "/chat", json={"messages": [...]}) as r:
            assert r.status_code == 200
            chunks = [c async for c in r.aiter_text()]
            assert any('"type": "message_end"' in c for c in chunks)
```

### 5. Storage round-trip

```python
async def test_memory_storage_roundtrip():
    from chatbot.storage.memory import InMemoryStorage
    s = InMemoryStorage()
    await s.save("conv_1", [{"role": "user", "content": "hi"}])
    assert await s.load("conv_1") == [{"role": "user", "content": "hi"}]
```

## Conventions

- **Fixtures first.** Look at `tests/conftest.py` before creating new ones —
  shared fixtures should be promoted there.
- **One concept per test.** A test asserts one behaviour. If you need to
  assert across phases, split into multiple tests with descriptive names.
- **Mock at the boundary.** Mock HTTP via `httpx_mock` or `respx`; mock LLM
  providers via `MockProvider` / `scripted_provider`, **not** by patching
  `httpx` internals.
- **Reproduce the bug first.** For bugfixes, write a failing test that
  captures the bug, confirm it fails, then apply the fix.
- **No skipped tests** unless gated on a missing service (Postgres / Redis)
  via `pytest.importorskip` or an env-var check.

## Running what you wrote

```bash
# The single test you just added
pytest tests/test_<area>.py::test_<name> -v

# The whole module
pytest tests/test_<area>.py -v

# Full suite, stop on first failure
pytest -x

# With coverage on the area you touched
pytest tests/ --cov=chatbot.<module> --cov-report=term-missing
```

## Common mistakes to avoid

- Marking async tests with `@pytest.mark.asyncio` (not needed — auto mode).
- Calling the real Anthropic / OpenAI API. Use `MockProvider` instead.
- Reading from `os.environ` directly inside tests — set env via
  `monkeypatch.setenv` so it's scoped to the test.
- Spinning up uvicorn for an integration test. Use `httpx.AsyncClient(app=...)`.
