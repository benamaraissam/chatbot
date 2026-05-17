"""Multimodal message part conversion."""

import base64

from chatbot.protocol.multimodal import parts_to_plain_summary, parts_to_provider_content
from chatbot.protocol.schemas import FilePart, ImagePart, TextPart

_MIN_PNG = base64.b64encode(
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
).decode()

_MIN_JPEG = base64.b64encode(
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"
).decode()


def test_text_only_content_is_string():
    content = parts_to_provider_content([TextPart(text="Hello")])
    assert content == "Hello"


def test_image_part_openai_format():
    content = parts_to_provider_content(
        [
            TextPart(text="What is this?"),
            ImagePart(mimeType="image/png", data=_MIN_PNG, name="shot.png"),
        ]
    )
    assert isinstance(content, list)
    assert content[0]["type"] == "image_url"
    assert content[0]["image_url"]["url"] == f"data:image/png;base64,{_MIN_PNG}"
    assert content[1] == {"type": "text", "text": "What is this?"}


def test_image_only_adds_default_prompt():
    content = parts_to_provider_content(
        [ImagePart(mimeType="image/jpeg", data=_MIN_JPEG, name="photo.jpg")]
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


def test_text_plain_image_part_is_inlined_not_image_url():
    raw = "hello from a text file"
    data = base64.b64encode(raw.encode()).decode()
    content = parts_to_provider_content(
        [ImagePart(mimeType="text/plain; charset=utf-8", data=data, name="fake.png")]
    )
    assert isinstance(content, str)
    assert "hello from a text file" in content
    assert "image_url" not in str(content)


def test_mislabeled_text_bytes_with_image_mime_is_inlined():
    raw = "not really a png"
    data = base64.b64encode(raw.encode()).decode()
    content = parts_to_provider_content(
        [ImagePart(mimeType="image/png", data=data, name="notes.png")]
    )
    assert isinstance(content, str)
    assert "not really a png" in content


def test_real_png_still_sent_as_image_url():
    # Minimal valid PNG header + IHDR chunk padding
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    )
    data = base64.b64encode(png).decode()
    content = parts_to_provider_content(
        [TextPart(text="see image"), ImagePart(mimeType="image/png", data=data, name="x.png")]
    )
    assert isinstance(content, list)
    assert content[0]["type"] == "image_url"
    assert content[0]["image_url"]["url"].startswith("data:image/png;base64,")


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
