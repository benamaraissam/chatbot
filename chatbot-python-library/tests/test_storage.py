"""Storage adapter tests."""

import pytest

from chatbot.storage.memory import MemoryStorage
from chatbot.storage.sqlite import SQLiteStorage
from chatbot.storage.base import MessageRecord


@pytest.mark.asyncio
async def test_memory_storage():
    storage = MemoryStorage()
    await storage.create_conversation("c1", "u1")
    await storage.append_message(
        MessageRecord(id="m1", conversation_id="c1", role="user", content="hi"),
    )
    msgs = await storage.get_messages("c1")
    assert len(msgs) == 1
    assert msgs[0].content == "hi"


@pytest.mark.asyncio
async def test_sqlite_storage(tmp_path):
    db = tmp_path / "test.db"
    storage = SQLiteStorage(f"sqlite:///{db}")
    await storage.create_conversation("c2")
    await storage.append_message(
        MessageRecord(id="m2", conversation_id="c2", role="user", content="sqlite"),
    )
    msgs = await storage.get_messages("c2")
    assert msgs[0].content == "sqlite"
