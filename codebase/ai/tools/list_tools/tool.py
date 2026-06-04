from __future__ import annotations

from typing import Any

from tools._learning_assistant import list_tools_impl


def list_tools(**_kwargs: Any) -> dict[str, Any]:
    return list_tools_impl()
