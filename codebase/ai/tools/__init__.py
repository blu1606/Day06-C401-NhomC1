from __future__ import annotations

from typing import Any

from .explain.tool import explain
from .summarize.tool import summarize


TOOL_FUNCTIONS: dict[str, Any] = {
    "explain": explain,
    "summarize": summarize,
}
