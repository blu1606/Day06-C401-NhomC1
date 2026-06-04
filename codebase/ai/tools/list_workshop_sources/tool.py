from __future__ import annotations

from typing import Any

from tools._learning_assistant import list_workshop_sources_impl


def list_workshop_sources(
    cohort: str | None = None,
    workshopNo: int | None = None,
    status: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return list_workshop_sources_impl(
        cohort=cohort,
        workshopNo=workshopNo,
        status=status,
        **kwargs,
    )
