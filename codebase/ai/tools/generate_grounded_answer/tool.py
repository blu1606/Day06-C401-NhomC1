from __future__ import annotations

from typing import Any

from tools._learning_assistant import generate_grounded_answer_impl


def generate_grounded_answer(
    question: str = "",
    sources: list[dict[str, Any]] | None = None,
    studentLevel: str = "beginner",
    language: str = "vi",
    **kwargs: Any,
) -> dict[str, Any]:
    return generate_grounded_answer_impl(
        question=question,
        sources=sources,
        studentLevel=studentLevel,
        language=language,
        **kwargs,
    )
