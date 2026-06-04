from __future__ import annotations

from typing import Any

from tools._learning_assistant import retrieve_slide_sources_impl


def retrieve_slide_sources(
    question: str = "",
    cohort: str | None = None,
    workshopNo: int | None = None,
    topK: int = 3,
    **kwargs: Any,
) -> dict[str, Any]:
    return retrieve_slide_sources_impl(
        question=question,
        cohort=cohort,
        workshopNo=workshopNo,
        topK=topK,
        **kwargs,
    )
