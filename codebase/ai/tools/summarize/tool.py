from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools._shared import ROOT, fold_text, terms


DATA_PATH = ROOT / "02-group-spec" / "data" / "mock_ai_tutor_slide_sources.json"
HIGH_CONFIDENCE_SCORE = 5
LOW_CONFIDENCE_SCORE = 3
STRONG_SINGLE_TERMS = {"rag", "chunking"}

FIELD_WEIGHTS = {
    "skill_tags": 4,
    "section_title": 3,
    "example_student_questions": 3,
    "summary": 2,
    "source_excerpt": 2,
    "workshop_title": 1,
}


def summarize(
    query: str = "",
    mode: str = "auto",
    workshop_no: int | None = None,
    max_sources: int = 3,
) -> dict[str, Any]:
    try:
        if _is_lab_answer_request(query):
            return _guardrail_response()

        sources = _load_sources(DATA_PATH)
        resolved_workshop_no = workshop_no or _extract_workshop_no(query)
        resolved_mode = _resolve_mode(mode, query, resolved_workshop_no)

        if resolved_mode == "workshop":
            return _summarize_workshop(
                query=query,
                sources=sources,
                workshop_no=resolved_workshop_no,
                max_sources=max_sources,
            )

        ranked = _rank_sources(query, sources, workshop_no=workshop_no)
        selected = ranked[:1]

        if not selected or _is_low_confidence_match(selected[0]):
            return _low_confidence_response(query)

        confidence = "high" if selected[0]["score"] >= HIGH_CONFIDENCE_SCORE else "low"
        citations = [_citation(item["source"]) for item in selected]
        primary = selected[0]["source"]

        return {
            "tool": "summarize",
            "query": query,
            "mode": "concept",
            "confidence": confidence,
            "summary": _summary(primary),
            "key_points": _key_points(primary),
            "citations": citations,
            "matches": [
                {
                    "source_id": item["source"]["source_id"],
                    "score": item["score"],
                    "matched_terms": item["matched_terms"],
                }
                for item in selected
            ],
        }
    except Exception as exc:
        return {"tool": "summarize", "error": type(exc).__name__, "message": str(exc)}


def _summarize_workshop(
    query: str,
    sources: list[dict[str, Any]],
    workshop_no: int | None,
    max_sources: int,
) -> dict[str, Any]:
    if workshop_no is None:
        return _low_confidence_response(query)

    selected_sources = [
        source for source in sources if source.get("workshop_no") == workshop_no
    ]
    selected_sources.sort(key=lambda source: source.get("slide_no", 0))
    selected_sources = selected_sources[: max(1, int(max_sources or 3))]

    if not selected_sources:
        return _low_confidence_response(query)

    return {
        "tool": "summarize",
        "query": query,
        "mode": "workshop",
        "confidence": "high",
        "summary": _workshop_summary(selected_sources),
        "key_points": _workshop_key_points(selected_sources),
        "citations": [_citation(source) for source in selected_sources],
        "matches": [
            {
                "source_id": source["source_id"],
                "score": 0,
                "matched_terms": ["workshop", str(workshop_no)],
            }
            for source in selected_sources
        ],
    }


def _load_sources(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        record
        for record in payload.get("records", [])
        if record.get("status") == "published"
    ]


def _rank_sources(
    query: str,
    sources: list[dict[str, Any]],
    workshop_no: int | None = None,
) -> list[dict[str, Any]]:
    query_terms = terms(query)
    ranked: list[dict[str, Any]] = []

    for source in sources:
        if workshop_no is not None and source.get("workshop_no") != workshop_no:
            continue

        score = 0
        matched_terms: set[str] = set()
        for field, weight in FIELD_WEIGHTS.items():
            overlap = query_terms & terms(_field_text(source.get(field)))
            if overlap:
                score += len(overlap) * weight
                matched_terms.update(overlap)

        if workshop_no is not None:
            score += 2

        if score:
            ranked.append(
                {
                    "source": source,
                    "score": score,
                    "matched_terms": sorted(matched_terms),
                }
            )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked


def _is_low_confidence_match(match: dict[str, Any]) -> bool:
    matched_terms = match.get("matched_terms", [])
    if match["score"] < LOW_CONFIDENCE_SCORE:
        return True
    if len(matched_terms) < 2 and not (set(matched_terms) & STRONG_SINGLE_TERMS):
        return True
    return False


def _resolve_mode(mode: str, query: str, workshop_no: int | None) -> str:
    normalized_mode = (mode or "auto").strip().lower()
    if normalized_mode in {"concept", "workshop"}:
        return normalized_mode
    folded = fold_text(query)
    if workshop_no is not None and any(token in folded for token in ["workshop", "buoi", "slide"]):
        return "workshop"
    return "concept"


def _extract_workshop_no(query: str) -> int | None:
    folded = fold_text(query)
    match = re.search(r"\b(?:workshop|ws|buoi)\s*(\d{1,2})\b", folded)
    if match:
        return int(match.group(1))
    return None


def _field_text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return "" if value is None else str(value)


def _summary(source: dict[str, Any]) -> str:
    return f"{source['section_title']}: {source['summary']}"


def _key_points(source: dict[str, Any]) -> list[str]:
    return [
        source["learning_objective"],
        source["summary"],
        source["source_excerpt"],
    ]


def _workshop_summary(sources: list[dict[str, Any]]) -> str:
    workshop_title = sources[0]["workshop_title"]
    workshop_no = sources[0]["workshop_no"]
    sections = ", ".join(source["section_title"] for source in sources)
    return f"Workshop {workshop_no} - {workshop_title}: gom cac phan chinh {sections}."


def _workshop_key_points(sources: list[dict[str, Any]]) -> list[str]:
    return [
        f"Slide {source['slide_no']} - {source['section_title']}: {source['summary']}"
        for source in sources
    ]


def _citation(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source["source_id"],
        "citation_label": source["citation_label"],
        "source_excerpt": source["source_excerpt"],
    }


def _low_confidence_response(query: str) -> dict[str, Any]:
    return {
        "tool": "summarize",
        "query": query,
        "mode": "unknown",
        "confidence": "low",
        "summary": (
            "Chua tim thay noi dung phu hop trong tai lieu chinh thuc. "
            "Hay hoi cu the hon hoac chon workshop lien quan."
        ),
        "key_points": [],
        "citations": [],
        "matches": [],
    }


def _guardrail_response() -> dict[str, Any]:
    return {
        "tool": "summarize",
        "confidence": "low",
        "summary": (
            "Tool summarize khong lam ho bai lab hoan chinh. "
            "Hay gui chu de, slide, hoac phan ban dang ket de tool tom tat kien thuc lien quan."
        ),
        "key_points": [],
        "citations": [],
        "matches": [],
    }


def _is_lab_answer_request(query: str) -> bool:
    folded = fold_text(query)
    risky_phrases = [
        "lam ho",
        "giai ho",
        "viet ho",
        "dap an lab",
        "bai nop hoan chinh",
        "code hoan chinh",
    ]
    return any(phrase in folded for phrase in risky_phrases)
