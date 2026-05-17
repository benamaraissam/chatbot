"""Public Chatbot API — library mode and HTTP handler entry point."""

from __future__ import annotations

import inspect
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, NamedTuple

from chatbot.core.agent import AgentLoop
from chatbot.core.context import Secrets, ToolContext, UserContext, UserContextProvider
from chatbot.core.events import Done, ErrorEvent, MessageStart, StreamEvent, TextDelta
from chatbot.mcp.registry import MCPRegistry, MCPServer
from chatbot.protocol.schemas import ChatRequest, Message, TextPart
from chatbot.providers.base import ProviderConfig, ProviderMessage, ProviderRegistry, build_default_registry
from chatbot.storage.base import ConversationStorage, MessageRecord
from chatbot.storage.sqlite import create_storage
from chatbot.tools.registry import ToolRegistry

DEFAULT_PROVIDERS: dict[str, dict[str, Any]] = {
    "mock": {"model": "mock"},
    "claude": {"model": "claude-sonnet-4-20250514", "api_key_env": "ANTHROPIC_API_KEY"},
}


class Conversation:
    """Handle for a multi-turn conversation."""

    def __init__(self, bot: Chatbot, conversation_id: str, user_context: dict[str, Any] | None = None) -> None:
        self._bot = bot
        self.id = conversation_id
        self._user_context = user_context or {}

    async def send(self, text: str, **kwargs: Any) -> "ChatbotResponse":
        return await self._bot.send(text, conversation_id=self.id, user_context=self._user_context, **kwargs)

    async def stream(self, text: str, **kwargs: Any) -> AsyncIterator[StreamEvent]:
        async for event in self._bot.stream(
            text, conversation_id=self.id, user_context=self._user_context, **kwargs
        ):
            yield event


class ResolvedProvider(NamedTuple):
    """Provider instance plus optional per-request model override."""

    provider: Any
    model: str | None = None


@dataclass
class ChatbotResponse:
    text: str
    conversation_id: str | None = None
    message_id: str | None = None
    usage: dict[str, int] | None = None


class Chatbot:
    """
    Main entry point for the chatbot library.

    Supports:
    - bot.send() / bot.stream() — library mode
    - bot.handle_request() — used by framework adapters
    - bot.conversation(id) — multi-turn
    """

    def __init__(
        self,
        *,
        provider: str | None = None,
        providers: dict[str, ProviderConfig | dict[str, Any]] | None = None,
        default_provider: str = "mock",
        tools: ToolRegistry | None = None,
        mcp_servers: list[MCPServer] | None = None,
        system_prompt: str | None = None,
        storage: str | None = "memory",
        secrets: Secrets | None = None,
    ) -> None:
        configs = providers or DEFAULT_PROVIDERS
        if provider and provider not in configs:
            configs = {**configs, provider: configs.get(default_provider, {"model": "mock"})}

        self._registry = build_default_registry(configs)
        self._default_provider = provider or default_provider
        self.tools = tools or ToolRegistry()
        self.system_prompt = system_prompt or "You are a helpful assistant."
        self.secrets = secrets or Secrets()
        self._storage = create_storage(storage)
        self._mcp = MCPRegistry(mcp_servers) if mcp_servers else None
        self._mcp_loaded = False

    @property
    def providers(self) -> ProviderRegistry:
        return self._registry

    def conversation(self, id: str | None = None, user_context: dict[str, Any] | None = None) -> Conversation:
        conv_id = id or f"conv_{uuid.uuid4().hex[:12]}"
        return Conversation(self, conv_id, user_context)

    async def _ensure_mcp_tools(self) -> None:
        if self._mcp and not self._mcp_loaded:
            await self._mcp.load_tools_into(self.tools)
            self._mcp_loaded = True

    def _resolve_user(self, user_context: dict[str, Any] | None) -> UserContext:
        ctx = user_context or {}
        user_id = str(ctx.get("user_id", ctx.get("id", "anonymous")))
        oauth_tokens = ctx.pop("_oauth_tokens", {}) if isinstance(ctx.get("_oauth_tokens"), dict) else {}
        user = UserContext(
            id=user_id,
            email=ctx.get("email"),
            metadata={k: v for k, v in ctx.items() if k not in ("user_id", "id", "email")},
        )
        user.oauth_tokens = oauth_tokens
        return user

    def _build_tool_context(
        self,
        user_context: dict[str, Any] | None,
        conversation_id: str | None,
    ) -> ToolContext:
        return ToolContext(
            user=self._resolve_user(user_context),
            conversation_id=conversation_id,
            secrets=self.secrets,
            metadata=user_context or {},
        )

    def _messages_to_provider(self, messages: list[Message]) -> list[ProviderMessage]:
        from chatbot.protocol.multimodal import parts_to_provider_content

        result: list[ProviderMessage] = []
        for msg in messages:
            if msg.role not in ("user", "assistant", "system"):
                continue
            content = parts_to_provider_content(msg.parts)
            if content:
                result.append(ProviderMessage(role=msg.role, content=content))
        return result

    def _resolve_provider(self, model: str | None = None) -> ResolvedProvider:
        """
        Resolve provider and optional model override from request.

        - ``None`` → default provider, configured model
        - Exact match on ``config.model`` → that provider
        - Provider name (``openai``, ``gpt``, ``claude``) → that provider
        - ``provider:model`` → provider with model override
        - Any other string → default provider with model override (custom model)
        """
        if not model:
            return ResolvedProvider(self._registry.get(self._default_provider))

        for prov in self._registry._providers.values():
            if prov.config.model == model:
                return ResolvedProvider(prov)

        if model in self._registry._providers:
            return ResolvedProvider(self._registry.get(model))

        if ":" in model:
            provider_name, model_name = model.split(":", 1)
            if provider_name in self._registry._providers:
                return ResolvedProvider(self._registry.get(provider_name), model_name or None)

        return ResolvedProvider(self._registry.get(self._default_provider), model)

    async def send(
        self,
        text: str,
        *,
        conversation_id: str | None = None,
        user_context: dict[str, Any] | None = None,
        model: str | None = None,
    ) -> ChatbotResponse:
        parts: list[str] = []
        msg_id: str | None = None
        usage: dict[str, int] | None = None
        async for event in self.stream(
            text, conversation_id=conversation_id, user_context=user_context, model=model
        ):
            if isinstance(event, TextDelta):
                parts.append(event.delta)
            if isinstance(event, MessageStart):
                msg_id = event.id
            if event.event_type == "message_end":
                usage = getattr(event, "usage", None)
        return ChatbotResponse(
            text="".join(parts),
            conversation_id=conversation_id,
            message_id=msg_id,
            usage=usage,
        )

    async def stream(
        self,
        text: str,
        *,
        conversation_id: str | None = None,
        user_context: dict[str, Any] | None = None,
        model: str | None = None,
        messages: list[Message] | None = None,
    ) -> AsyncIterator[StreamEvent]:
        await self._ensure_mcp_tools()

        conv_id = conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
        await self._storage.create_conversation(conv_id, user_context.get("user_id") if user_context else None)

        if messages is None:
            messages = [
                Message(
                    id=f"msg_{uuid.uuid4().hex[:8]}",
                    role="user",
                    parts=[TextPart(text=text)],
                )
            ]

        user_msg = messages[-1]
        from chatbot.protocol.multimodal import parts_to_plain_summary

        content = parts_to_plain_summary(user_msg.parts)
        await self._storage.append_message(
            MessageRecord(
                id=user_msg.id,
                conversation_id=conv_id,
                role="user",
                content=content,
            )
        )

        history = await self._storage.get_messages(conv_id)
        provider_messages = [
            ProviderMessage(role=m.role, content=m.content) for m in history if m.role in ("user", "assistant")
        ]

        ctx = self._build_tool_context(user_context, conv_id)
        resolved = self._resolve_provider(model)
        agent = AgentLoop(resolved.provider, self.tools, system_prompt=self.system_prompt)

        assistant_text: list[str] = []
        try:
            async for event in agent.run(provider_messages, ctx, model=resolved.model):
                if isinstance(event, StreamEvent) and event.event_type == "text_delta":
                    assistant_text.append(event.to_payload().get("delta", ""))  # type: ignore
                yield event
        except Exception as exc:
            yield ErrorEvent(code="agent_error", message=str(exc))
        else:
            if assistant_text:
                await self._storage.append_message(
                    MessageRecord(
                        id=f"msg_{uuid.uuid4().hex[:8]}",
                        conversation_id=conv_id,
                        role="assistant",
                        content="".join(assistant_text),
                    )
                )
        yield Done()

    async def handle_request(
        self,
        request: ChatRequest,
        user_context: dict[str, Any] | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """Handle HTTP ChatRequest — used by framework adapters."""
        await self._ensure_mcp_tools()
        conv_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
        merged_context = {**request.metadata, **(user_context or {})}
        ctx = self._build_tool_context(merged_context, conv_id)

        provider_messages = self._messages_to_provider(request.messages)
        if not provider_messages:
            yield ErrorEvent(code="invalid_request", message="No messages provided")
            yield Done()
            return

        resolved = self._resolve_provider(request.model)
        agent = AgentLoop(resolved.provider, self.tools, system_prompt=self.system_prompt)

        approved_raw = request.metadata.get("approved_tool_ids") or request.metadata.get(
            "approvedToolIds"
        )
        approved_tool_ids: set[str] | None = None
        if isinstance(approved_raw, list):
            approved_tool_ids = {str(x) for x in approved_raw}

        try:
            async for event in agent.run(
                provider_messages,
                ctx,
                model=resolved.model,
                approved_tool_ids=approved_tool_ids,
            ):
                yield event
        except Exception as exc:
            yield ErrorEvent(code="agent_error", message=str(exc))
        yield Done()

    async def handle_request_with_provider(
        self,
        request: ChatRequest,
        user_context_provider: UserContextProvider | Callable[..., dict[str, Any]],
        **provider_kwargs: Any,
    ) -> AsyncIterator[StreamEvent]:
        user_ctx = await _resolve_user_context(user_context_provider, **provider_kwargs)
        async for event in self.handle_request(request, user_ctx):
            yield event


def _filter_provider_kwargs(
    provider: UserContextProvider | Callable[..., Any],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Pass only kwargs the user_context callable accepts (e.g. optional ``request``)."""
    sig = inspect.signature(provider)
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
        return kwargs
    return {name: value for name, value in kwargs.items() if name in sig.parameters}


async def _resolve_user_context(
    provider: UserContextProvider | Callable[..., Any],
    **kwargs: Any,
) -> dict[str, Any]:
    call_kwargs = _filter_provider_kwargs(provider, kwargs)
    result = provider(**call_kwargs)
    if isinstance(result, Awaitable):
        result = await result
    if isinstance(result, UserContext):
        return {
            "user_id": result.id,
            "email": result.email,
            **result.metadata,
            "_oauth_tokens": result.oauth_tokens,
        }
    return dict(result)
