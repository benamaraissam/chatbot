"""Built-in tool: generate a downloadable file and return it as a FilePart."""

from __future__ import annotations

import base64

from chatbot.core.context import ToolContext
from chatbot.protocol.schemas import FilePart
from chatbot.tools.registry import RegisteredTool

# Maps the user-facing format name → (file extension, MIME type)
_FORMAT_MAP: dict[str, tuple[str, str]] = {
    "csv": ("csv", "text/csv"),
    "json": ("json", "application/json"),
    "txt": ("txt", "text/plain"),
    "md": ("md", "text/markdown"),
    "html": ("html", "text/html"),
    "xml": ("xml", "application/xml"),
    "tsv": ("tsv", "text/tab-separated-values"),
    "yaml": ("yaml", "text/yaml"),
    "yml": ("yml", "text/yaml"),
}


async def _generate_file(
    ctx: ToolContext,
    content: str,
    filename: str,
    format: str = "txt",
) -> FilePart:
    """
    Generate a downloadable file from the given text content.

    Returns a FilePart that will be surfaced as a download button in the chat UI.
    """
    fmt = format.lower().lstrip(".")
    ext, mime_type = _FORMAT_MAP.get(fmt, (fmt, "application/octet-stream"))

    # Ensure the filename has the right extension
    if not filename.lower().endswith(f".{ext}"):
        filename = f"{filename}.{ext}"

    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    return FilePart(name=filename, mime_type=mime_type, data=encoded)


generate_file_tool = RegisteredTool(
    name="generate_file",
    description=(
        "Generate a downloadable file from text content. "
        "Use this whenever the user asks to download data in a specific format "
        "(CSV, JSON, TXT, Markdown, HTML, XML, TSV, YAML, etc.). "
        "Returns a file the user can download directly from the chat."
    ),
    parameters_schema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The full text content of the file.",
            },
            "filename": {
                "type": "string",
                "description": (
                    "Desired filename without extension, e.g. 'report' or 'data_export'. "
                    "The correct extension will be appended automatically."
                ),
            },
            "format": {
                "type": "string",
                "description": (
                    "File format: csv, json, txt, md, html, xml, tsv, yaml. "
                    "Defaults to txt."
                ),
                "default": "txt",
            },
        },
        "required": ["content", "filename"],
    },
    fn=_generate_file,
)
