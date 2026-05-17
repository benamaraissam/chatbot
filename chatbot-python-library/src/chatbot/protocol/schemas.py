"""Pydantic schemas for the chatbot HTTP protocol (v1)."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

PROTOCOL_VERSION = "1"


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImagePart(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Literal["image"] = "image"
    mime_type: str = Field(
        validation_alias=AliasChoices("mimeType", "mime_type"),
        serialization_alias="mimeType",
    )
    data: str
    name: str | None = None


class FilePart(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Literal["file"] = "file"
    name: str
    mime_type: str = Field(
        validation_alias=AliasChoices("mimeType", "mime_type"),
        serialization_alias="mimeType",
    )
    data: str


MessagePart = Annotated[
    TextPart | ImagePart | FilePart,
    Field(discriminator="type"),
]


class Message(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    role: Literal["user", "assistant", "system", "tool"]
    parts: list[MessagePart] = Field(default_factory=list)


class ChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    messages: list[Message]
    conversation_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("conversationId", "conversation_id"),
        serialization_alias="conversationId",
    )
    model: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UsageInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    """Non-streaming response (optional endpoint)."""

    model_config = ConfigDict(populate_by_name=True)

    message: Message
    conversation_id: str | None = Field(default=None, alias="conversationId")
    usage: UsageInfo | None = None
    finish_reason: str | None = Field(
        default=None,
        validation_alias=AliasChoices("finishReason", "finish_reason"),
        serialization_alias="finishReason",
    )
