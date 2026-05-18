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

# Moonshot / OpenAI vision: raster formats only (not SVG, not text sniffed as image).
_SUPPORTED_IMAGE_MIMES = frozenset(
    {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
    }
)


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
            if _should_send_as_image_url(part.mime_type, part.data):
                url = _image_data_url(part.mime_type, part.data)
                image_blocks.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": url, "detail": "auto"},
                    }
                )
            else:
                other_blocks.append(
                    {
                        "type": "text",
                        "text": _non_image_attachment_text(
                            part.name, part.mime_type, part.data
                        ),
                    }
                )
        elif isinstance(part, FilePart):
            if _should_send_as_image_url(part.mime_type, part.data):
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


def provider_content_to_text(content: str | list[dict[str, Any]] | None) -> str:
    """Flatten provider message content for scenario matching / logging."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    bits: list[str] = []
    for block in content:
        if block.get("type") == "text":
            bits.append(str(block.get("text", "")))
        elif block.get("type") == "image_url":
            bits.append("[Image]")
    return " ".join(bits).strip()


def _mime_base(mime_type: str) -> str:
    return mime_type.split(";")[0].strip().lower()


def _decode_attachment_bytes(data: str) -> bytes:
    payload = data.split(",", 1)[-1] if data.startswith("data:") else data
    return base64.b64decode(payload, validate=False)


def _looks_like_raster_image(data: str) -> bool:
    try:
        raw = _decode_attachment_bytes(data)[:16]
    except Exception:
        return False
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if raw.startswith(b"\xff\xd8\xff"):
        return True
    if raw.startswith(b"GIF87a") or raw.startswith(b"GIF89a"):
        return True
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return True
    return False


def _should_send_as_image_url(mime_type: str, data: str) -> bool:
    base = _mime_base(mime_type)
    if not base.startswith("image/"):
        return False
    if base not in _SUPPORTED_IMAGE_MIMES:
        return False
    return _looks_like_raster_image(data)


def _image_data_url(mime_type: str, data: str) -> str:
    payload = data.split(",", 1)[-1] if data.startswith("data:") else data
    base = _mime_base(mime_type) or "image/jpeg"
    if base not in _SUPPORTED_IMAGE_MIMES:
        base = "image/jpeg"
    return f"data:{base};base64,{payload}"


def _non_image_attachment_text(name: str | None, mime_type: str, data: str) -> str:
    label = name or "attachment"
    if _mime_base(mime_type).startswith("text/") or _looks_like_utf8_text(data):
        try:
            text = _decode_attachment_bytes(data).decode("utf-8", errors="replace")
            if len(text) > _MAX_INLINE_FILE_CHARS:
                text = text[:_MAX_INLINE_FILE_CHARS] + "\n… (truncated)"
            return f"Attached file `{label}`:\n\n```\n{text}\n```"
        except Exception:
            pass
    return (
        f"[Attached file: {label} ({mime_type}). "
        "Could not be sent as an image; paste text or use PNG/JPEG/WebP/GIF.]"
    )


def _looks_like_utf8_text(data: str) -> bool:
    try:
        raw = _decode_attachment_bytes(data)[:512]
    except Exception:
        return False
    if not raw:
        return False
    if b"\x00" in raw:
        return False
    try:
        raw.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


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
