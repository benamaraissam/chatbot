"""Storage adapter interface for conversation persistence."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class MessageRecord:
    id: str
    conversation_id: str
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ConversationStorage(ABC):
    @abstractmethod
    async def get_messages(self, conversation_id: str, limit: int = 100) -> list[MessageRecord]:
        ...

    @abstractmethod
    async def append_message(self, record: MessageRecord) -> None:
        ...

    @abstractmethod
    async def create_conversation(self, conversation_id: str, user_id: str | None = None) -> None:
        ...

    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> None:
        ...
