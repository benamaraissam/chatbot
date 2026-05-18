"""SQLite conversation storage."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from chatbot.storage.base import ConversationStorage, MessageRecord


class SQLiteStorage(ConversationStorage):
    def __init__(self, dsn: str = "sqlite:///./chatbot.db") -> None:
        path = dsn.replace("sqlite:///", "")
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._path))

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                );
                CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
                """
            )

    async def get_messages(self, conversation_id: str, limit: int = 100) -> list[MessageRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, conversation_id, role, content, metadata, created_at
                FROM messages WHERE conversation_id = ?
                ORDER BY created_at ASC LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()
        return [_row_to_record(r) for r in rows]

    async def append_message(self, record: MessageRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO messages
                    (id, conversation_id, role, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.conversation_id,
                    record.role,
                    record.content,
                    json.dumps(record.metadata),
                    record.created_at.isoformat(),
                ),
            )

    async def create_conversation(self, conversation_id: str, user_id: str | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO conversations (id, user_id, created_at) VALUES (?, ?, ?)",
                (conversation_id, user_id, datetime.now(UTC).isoformat()),
            )

    async def delete_conversation(self, conversation_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))


def _row_to_record(row: tuple) -> MessageRecord:
    meta = json.loads(row[4]) if row[4] else {}
    created = datetime.fromisoformat(row[5])
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return MessageRecord(
        id=row[0],
        conversation_id=row[1],
        role=row[2],
        content=row[3],
        metadata=meta,
        created_at=created,
    )


def create_storage(dsn: str | None) -> ConversationStorage:
    from chatbot.storage.memory import MemoryStorage

    if not dsn or dsn == "memory":
        return MemoryStorage()
    if dsn.startswith("sqlite:"):
        return SQLiteStorage(dsn)
    if dsn.startswith("postgres:"):
        from chatbot.storage.postgres import PostgresStorage

        return PostgresStorage(dsn)
    return MemoryStorage()
