"""In-memory conversation storage (default for tests)."""

from __future__ import annotations

from chatbot.storage.base import ConversationStorage, MessageRecord


class MemoryStorage(ConversationStorage):
    def __init__(self) -> None:
        self._messages: dict[str, list[MessageRecord]] = {}
        self._conversations: set[str] = set()

    async def get_messages(self, conversation_id: str, limit: int = 100) -> list[MessageRecord]:
        msgs = self._messages.get(conversation_id, [])
        return msgs[-limit:]

    async def append_message(self, record: MessageRecord) -> None:
        self._conversations.add(record.conversation_id)
        self._messages.setdefault(record.conversation_id, []).append(record)

    async def create_conversation(self, conversation_id: str, user_id: str | None = None) -> None:
        self._conversations.add(conversation_id)

    async def delete_conversation(self, conversation_id: str) -> None:
        self._conversations.discard(conversation_id)
        self._messages.pop(conversation_id, None)
