"""Built-in safe code interpreter (restricted eval for demos)."""

from __future__ import annotations

import ast
import math
from typing import Any

from chatbot.core.context import ToolContext
from chatbot.tools.registry import RegisteredTool

_SAFE_NAMES = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "sum": sum,
    "len": len,
    "math": math,
}


async def _code_interpreter(ctx: ToolContext, code: str) -> Any:
    """
    Execute a short Python expression safely (no imports, no file I/O).
    For production, replace with a sandboxed runtime.
    """
    tree = ast.parse(code, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Call)):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id not in _SAFE_NAMES and node.func.id not in dir(math):
                    raise ValueError(f"Disallowed call: {node.func.id}")
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                raise ValueError("Imports are not allowed")
    return eval(compile(tree, "<tool>", "eval"), {"__builtins__": {}}, dict(_SAFE_NAMES))


code_interpreter_tool = RegisteredTool(
    name="code_interpreter",
    description="Evaluate a safe Python mathematical expression.",
    parameters_schema={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python expression e.g. sum([1,2,3])"},
        },
        "required": ["code"],
    },
    fn=_code_interpreter,
    requires_approval=True,
    timeout=5.0,
)
