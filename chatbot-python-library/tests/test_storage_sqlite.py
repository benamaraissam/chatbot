"""Tests for chatbot.storage.sqlite — SQLite-backed conversation storage."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from chatbot.storage.base import MessageRecord
from chatbot.storage.sqlite import SQLiteStorage, create_storage


def _make_record(conv_id: str, msg_id: str, role: str = "user", content: str = "hi") -> MessageRecord:
    return MessageRecord(
        id=msg_id,
        conversation_id=conv_id,
        role=role,
        content=content,
        metadata={"trace": msg_id},
        created_at=datetime.now(UTC),
    )


# ─────────────────────────────────────────────────────────────────────────────
# SQLiteStorage
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path: Path) -> SQLiteStorage:
    return SQLiteStorage(f"sqlite:///{tmp_path / 'chatbot.db'}")


async def test_init_creates_schema_at_provided_path(tmp_path: Path) -> None:
    db = tmp_path / "nested" / "chatbot.db"
    SQLiteStorage(f"sqlite:///{db}")
    # The init step creates the parent directory and the file.
    assert db.exists()


async def test_append_and_get_messages_roundtrip(store: SQLiteStorage) -> None:
    await store.create_conversation("c_1", user_id="u_1")
    await store.append_message(_make_record("c_1", "m_1", content="hello"))
    await store.append_message(_make_record("c_1", "m_2", content="world"))

    msgs = await store.get_messages("c_1")
    assert [m.id for m in msgs] == ["m_1", "m_2"]
    assert msgs[0].content == "hello"
    assert msgs[1].metadata == {"trace": "m_2"}
    # created_at always becomes timezone-aware UTC after a round-trip.
    assert msgs[0].created_at.tzinfo is not None


async def test_get_messages_respects_limit(store: SQLiteStorage) -> None:
    await store.create_conversation("c_2")
    for i in range(5):
        await store.append_message(_make_record("c_2", f"m_{i}"))

    msgs = await store.get_messages("c_2", limit=3)
    assert len(msgs) == 3


async def test_get_messages_returns_empty_for_unknown_conversation(store: SQLiteStorage) -> None:
    assert await store.get_messages("missing") == []


async def test_append_replaces_existing_message_id(store: SQLiteStorage) -> None:
    await store.create_conversation("c_3")
    await store.append_message(_make_record("c_3", "m_dup", content="first"))
    await store.append_message(_make_record("c_3", "m_dup", content="second"))

    msgs = await store.get_messages("c_3")
    # INSERT OR REPLACE keeps a single row but with the new content.
    assert len(msgs) == 1
    assert msgs[0].content == "second"


async def test_delete_conversation_removes_messages_and_row(store: SQLiteStorage) -> None:
    await store.create_conversation("c_4")
    await store.append_message(_make_record("c_4", "m_1"))
    assert (await store.get_messages("c_4"))[0].id == "m_1"

    await store.delete_conversation("c_4")
    assert await store.get_messages("c_4") == []


async def test_create_conversation_is_idempotent(store: SQLiteStorage) -> None:
    await store.create_conversation("c_5", user_id="u_x")
    # Re-creating with the same id must not raise.
    await store.create_conversation("c_5", user_id="u_y")


# ─────────────────────────────────────────────────────────────────────────────
# create_storage factory
# ─────────────────────────────────────────────────────────────────────────────

def test_create_storage_default_returns_memory_backend() -> None:
    from chatbot.storage.memory import MemoryStorage

    assert isinstance(create_storage(None), MemoryStorage)
    assert isinstance(create_storage("memory"), MemoryStorage)


def test_create_storage_sqlite_returns_sqlite_backend(tmp_path: Path) -> None:
    s = create_storage(f"sqlite:///{tmp_path / 'cb.db'}")
    assert isinstance(s, SQLiteStorage)


def test_create_storage_unknown_dsn_returns_memory_backend() -> None:
    from chatbot.storage.memory import MemoryStorage

    # Unknown scheme silently falls back to memory rather than erroring.
    assert isinstance(create_storage("redis://localhost:6379/0"), MemoryStorage)
