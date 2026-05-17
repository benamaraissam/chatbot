"""Multimodal message part conversion."""

import base64

from chatbot.protocol.multimodal import parts_to_plain_summary, parts_to_provider_content
from chatbot.protocol.schemas import FilePart, ImagePart, TextPart


def test_text_only_content_is_string():
    content = parts_to_provider_content([TextPart(text="Hello")])
    assert content == "Hello"


def test_image_part_openai_format():
    content = parts_to_provider_content(
        [
            TextPart(text="What is this?"),
            ImagePart(mimeType="image/png", data="abc123", name="shot.png"),
        ]
    )
    assert isinstance(content, list)
    assert content[0]["type"] == "image_url"
    assert content[0]["image_url"]["url"] == "data:image/png;base64,abc123"
    assert content[1] == {"type": "text", "text": "What is this?"}


def test_image_only_adds_default_prompt():
    content = parts_to_provider_content(
        [ImagePart(mimeType="image/jpeg", data="xyz", name="photo.jpg")]
    )
    assert isinstance(content, list)
    assert content[0]["type"] == "image_url"
    assert content[1]["type"] == "text"
    assert "image" in content[1]["text"].lower()


def test_text_file_inlined():
    raw = "line one\nline two"
    data = base64.b64encode(raw.encode()).decode()
    content = parts_to_provider_content(
        [FilePart(name="notes.txt", mimeType="text/plain", data=data)]
    )
    assert isinstance(content, str)
    assert "line one" in content
    assert "notes.txt" in content


def test_plain_summary():
    summary = parts_to_plain_summary(
        [
            TextPart(text="Hi"),
            ImagePart(mimeType="image/jpeg", data="x", name="photo.jpg"),
            FilePart(name="doc.pdf", mimeType="application/pdf", data="y"),
        ]
    )
    assert "Hi" in summary
    assert "[Image: photo.jpg]" in summary
    assert "[File: doc.pdf]" in summary
