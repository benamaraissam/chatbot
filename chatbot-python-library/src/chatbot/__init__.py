"""chatbot — Framework-agnostic Python chatbot backend."""

from chatbot.core.chatbot import Chatbot, ChatbotResponse, Conversation
from chatbot.core.context import Secrets, ToolContext, UserContext, UserContextProvider
from chatbot.core.events import (
    Done,
    ErrorEvent,
    MessageEnd,
    MessageStart,
    StreamEvent,
    TextDelta,
    ToolApprovalRequired,
    ToolCallEnd,
    ToolCallStart,
    ToolResult,
)
from chatbot.mcp import MCPServer, MCPRegistry
from chatbot.protocol import ChatRequest, Message, MessagePart, PROTOCOL_VERSION
from chatbot.tools import BearerAuth, ToolRegistry, from_openapi, http_tool

__version__ = "0.1.0"

__all__ = [
    "BearerAuth",
    "ChatRequest",
    "Chatbot",
    "ChatbotResponse",
    "Conversation",
    "Done",
    "ErrorEvent",
    "MCPServer",
    "MCPRegistry",
    "Message",
    "MessageEnd",
    "MessagePart",
    "MessageStart",
    "PROTOCOL_VERSION",
    "Secrets",
    "StreamEvent",
    "TextDelta",
    "ToolApprovalRequired",
    "ToolCallEnd",
    "ToolCallStart",
    "ToolContext",
    "ToolRegistry",
    "ToolResult",
    "UserContext",
    "UserContextProvider",
    "from_openapi",
    "http_tool",
]
