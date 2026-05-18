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
from chatbot.mcp import MCPRegistry, MCPServer
from chatbot.protocol import PROTOCOL_VERSION, ChatRequest, Message, MessagePart
from chatbot.skills import Skill, SkillFrontmatter, SkillRegistry
from chatbot.tools import BearerAuth, ToolRegistry, from_openapi, http_tool, paginated

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
    "Skill",
    "SkillFrontmatter",
    "SkillRegistry",
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
    "paginated",
]
