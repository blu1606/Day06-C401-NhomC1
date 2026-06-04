from __future__ import annotations

from typing import Any

from .summarize.tool import summarize


TOOL_FUNCTIONS: dict[str, Any] = {
    "summarize": summarize,
}

