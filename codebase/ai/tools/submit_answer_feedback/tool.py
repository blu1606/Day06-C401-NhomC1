from __future__ import annotations

from typing import Any

from tools._learning_assistant import submit_answer_feedback_impl


def submit_answer_feedback(
    question: str = "",
    answerId: str | None = None,
    sourceIds: list[str] | None = None,
    feedbackType: str = "unclear_answer",
    note: str | None = None,
    userRole: str = "student",
    **kwargs: Any,
) -> dict[str, Any]:
    return submit_answer_feedback_impl(
        question=question,
        answerId=answerId,
        sourceIds=sourceIds,
        feedbackType=feedbackType,
        note=note,
        userRole=userRole,
        **kwargs,
    )
