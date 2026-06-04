from __future__ import annotations

from pathlib import Path
from typing import Any

from .explain.tool import explain

TOOL_FUNCTIONS = {
    "explain": explain,
}
