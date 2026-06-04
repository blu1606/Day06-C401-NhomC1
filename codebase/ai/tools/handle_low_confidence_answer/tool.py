from __future__ import annotations

from typing import Any

from tools._learning_assistant import handle_low_confidence_answer_impl


def handle_low_confidence_answer(
    question: str = "",
    reason: str = "",
    closestSources: list[dict[str, Any]] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return handle_low_confidence_answer_impl(
        question=question,
        reason=reason,
        closestSources=closestSources,
        **kwargs,
    )
