"""PostgreSQL conversation storage (optional extra)."""

from __future__ import annotations

import json
from typing import Any

from chatbot.storage.base import ConversationStorage, MessageRecord


class PostgresStorage(ConversationStorage):
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: Any = None

    async def _get_pool(self) -> Any:
        if self._pool is None:
            try:
                import asyncpg
            except ImportError as exc:
                raise ImportError("Install chatbot[postgres] for PostgreSQL storage") from exc
            self._pool = await asyncpg.create_pool(
                self._dsn.replace("postgres://", "postgresql://")
            )
            await self._init_schema()
        return self._pool

    async def _init_schema(self) -> None:
        pool = self._pool
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL REFERENCES conversations(id),
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

    async def get_messages(self, conversation_id: str, limit: int = 100) -> list[MessageRecord]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, conversation_id, role, content, metadata, created_at
                FROM messages WHERE conversation_id = $1
                ORDER BY created_at ASC LIMIT $2
                """,
                conversation_id,
                limit,
            )
        return [
            MessageRecord(
                id=r["id"],
                conversation_id=r["conversation_id"],
                role=r["role"],
                content=r["content"],
                metadata=r["metadata"] or {},
                created_at=r["created_at"],
            )
            for r in rows
        ]

    async def append_message(self, record: MessageRecord) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO messages (id, conversation_id, role, content, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content
                """,
                record.id,
                record.conversation_id,
                record.role,
                record.content,
                json.dumps(record.metadata),
                record.created_at,
            )

    async def create_conversation(self, conversation_id: str, user_id: str | None = None) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO conversations (id, user_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                conversation_id,
                user_id,
            )

    async def delete_conversation(self, conversation_id: str) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM messages WHERE conversation_id = $1", conversation_id)
            await conn.execute("DELETE FROM conversations WHERE id = $1", conversation_id)
