"""Convert protocol message parts to provider-native multimodal content."""

from __future__ import annotations

import base64
from typing import Any

from chatbot.protocol.schemas import FilePart, ImagePart, MessagePart, TextPart

_TEXT_FILE_SUFFIXES = (
    ".txt",
    ".md",
    ".json",
    ".csv",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".html",
    ".css",
    ".xml",
    ".yaml",
    ".yml",
    ".log",
)
_MAX_INLINE_FILE_CHARS = 12_000
_IMAGE_ONLY_DEFAULT_PROMPT = "What is in this image?"


def parts_to_provider_content(parts: list[MessagePart]) -> str | list[dict[str, Any]] | None:
    """Build OpenAI-compatible message content (string or content parts array)."""
    text_parts: list[TextPart] = []
    image_blocks: list[dict[str, Any]] = []
    other_blocks: list[dict[str, Any]] = []

    for part in parts:
        if isinstance(part, TextPart):
            if part.text.strip():
                text_parts.append(part)
        elif isinstance(part, ImagePart):
            url = _image_data_url(part.mime_type, part.data)
            image_blocks.append(
                {
                    "type": "image_url",
                    "image_url": {"url": url, "detail": "auto"},
                }
            )
        elif isinstance(part, FilePart):
            if part.mime_type.lower().startswith("image/"):
                url = _image_data_url(part.mime_type, part.data)
                image_blocks.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": url, "detail": "auto"},
                    }
                )
            else:
                other_blocks.append({"type": "text", "text": _file_part_to_text(part)})

    if not text_parts and image_blocks and not other_blocks:
        text_parts = [TextPart(text=_IMAGE_ONLY_DEFAULT_PROMPT)]

    blocks: list[dict[str, Any]] = []
    # Vision models (e.g. Kimi) work best with images before the text prompt.
    blocks.extend(image_blocks)
    for tp in text_parts:
        blocks.append({"type": "text", "text": tp.text})
    blocks.extend(other_blocks)

    if not blocks:
        return None
    if len(blocks) == 1 and blocks[0].get("type") == "text":
        return str(blocks[0]["text"])
    return blocks


def parts_to_plain_summary(parts: list[MessagePart]) -> str:
    """Short text summary for storage / logs."""
    bits: list[str] = []
    for part in parts:
        if isinstance(part, TextPart):
            bits.append(part.text)
        elif isinstance(part, ImagePart):
            label = part.name or "image"
            bits.append(f"[Image: {label}]")
        elif isinstance(part, FilePart):
            bits.append(f"[File: {part.name}]")
    return " ".join(bits).strip()


def provider_content_to_text(content: str | list[dict[str, Any]]) -> str:
    """Flatten provider message content for scenario matching / logging."""
    if isinstance(content, str):
        return content
    bits: list[str] = []
    for block in content:
        if block.get("type") == "text":
            bits.append(str(block.get("text", "")))
        elif block.get("type") == "image_url":
            bits.append("[Image]")
    return " ".join(bits).strip()


def _image_data_url(mime_type: str, data: str) -> str:
    payload = data.split(",", 1)[-1] if data.startswith("data:") else data
    mime = mime_type or "image/jpeg"
    return f"data:{mime};base64,{payload}"


def _file_part_to_text(part: FilePart) -> str:
    mime = part.mime_type.lower()
    name_lower = part.name.lower()
    inline = mime.startswith("text/") or any(name_lower.endswith(s) for s in _TEXT_FILE_SUFFIXES)
    if inline:
        try:
            raw = base64.b64decode(part.data.split(",", 1)[-1], validate=False)
            text = raw.decode("utf-8", errors="replace")
            if len(text) > _MAX_INLINE_FILE_CHARS:
                text = text[:_MAX_INLINE_FILE_CHARS] + "\n… (truncated)"
            return f"Attached file `{part.name}`:\n\n```\n{text}\n```"
        except Exception:
            pass
    return (
        f"[Attached file: {part.name} ({part.mime_type}). "
        "Binary file content was not inlined; ask the user to paste text if needed.]"
    )
