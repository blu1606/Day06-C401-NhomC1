from __future__ import annotations

from typing import Any

from tools._learning_assistant import classify_question_scope_impl


def classify_question_scope(
    question: str = "",
    retrievedMatches: list[dict[str, Any]] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return classify_question_scope_impl(
        question=question,
        retrievedMatches=retrievedMatches,
        **kwargs,
    )
