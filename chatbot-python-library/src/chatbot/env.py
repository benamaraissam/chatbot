"""Load ``.env`` files for local development (optional ``python-dotenv``)."""

from __future__ import annotations

from pathlib import Path


def load_dotenv_file(*paths: str | Path) -> bool:
    """
  Load environment variables from ``.env`` file(s).

  Returns True if python-dotenv loaded at least one existing file.
  Install: ``pip install python-dotenv`` (included in ``chatbot[server]``).
  """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    loaded = False
    for raw in paths:
        path = Path(raw)
        if path.is_file() and load_dotenv(path, override=False):
            loaded = True
    return loaded


def load_project_dotenv(start: str | Path | None = None) -> bool:
    """Load ``.env`` from package root (parent of ``src/chatbot``) or cwd."""
    candidates: list[Path] = []
    if start is not None:
        p = Path(start).resolve()
        candidates.append(p / ".env")
        if p.is_file():
            candidates.append(p.parent / ".env")
    here = Path(__file__).resolve()
    candidates.append(here.parents[2] / ".env")  # chatbot-python-library/
    candidates.append(Path.cwd() / ".env")
    seen: set[Path] = set()
    unique = []
    for c in candidates:
        c = c.resolve()
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return load_dotenv_file(*unique)
