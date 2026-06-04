from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools._shared import ROOT, fold_text, terms


SOURCE_PATHS = (
    ROOT / "02-group-spec" / "data" / "mock_ai_tutor_slide_sources.json",
    ROOT / "02-group-spec" / "data" / "day05_ai_tutor_slide_sources.json",
    ROOT / "codebase" / "data" / "day05_ai_tutor_slide_sources.json",
    ROOT / "codebase" / "frontend" / "data" / "slide_sources.json",
    ROOT / "codebase" / "frontend" / "data" / "day05_ai_tutor_slide_sources.json",
)

FIELD_WEIGHTS = {
    "skill_tags": 5,
    "section_title": 4,
    "example_student_questions": 4,
    "summary": 3,
    "source_excerpt": 3,
    "learning_objective": 2,
    "content": 1,
    "full_text": 1,
    "raw_text": 1,
}

IN_SCOPE_THRESHOLD = 0.55
LOW_CONFIDENCE_THRESHOLD = 0.25
FEEDBACK_LOG_PATH = Path(tempfile.gettempdir()) / "gaptutor_answer_feedback.jsonl"
OUT_OF_SCOPE_TERMS = {
    "chung khoan",
    "co phieu",
    "dau tu",
    "bitcoin",
    "crypto",
    "forex",
    "benh",
    "thuoc",
    "phap ly",
}

TOOL_DESCRIPTIONS: dict[str, dict[str, Any]] = {
    "retrieve_slide_sources": {
        "purpose": "Find the most relevant published slide/document sources for a student question.",
        "inputs": ["question", "cohort", "workshopNo", "topK"],
        "outputs": ["matches"],
    },
    "classify_question_scope": {
        "purpose": "Classify whether a question is answerable from official sources.",
        "inputs": ["question", "retrievedMatches"],
        "outputs": ["scope", "reason", "confidence"],
    },
    "generate_grounded_answer": {
        "purpose": "Generate a short answer grounded in retrieved sources with citations.",
        "inputs": ["question", "sources", "studentLevel", "language"],
        "outputs": ["answer", "example", "citations"],
    },
    "handle_low_confidence_answer": {
        "purpose": "Return a safe fallback when sources are missing or confidence is low.",
        "inputs": ["question", "reason", "closestSources"],
        "outputs": ["message", "suggestedQuestions"],
    },
    "submit_answer_feedback": {
        "purpose": "Save student/mentor/admin feedback as a correction signal.",
        "inputs": ["question", "answerId", "sourceIds", "feedbackType", "note", "userRole"],
        "outputs": ["saved", "feedbackId", "nextAction"],
    },
    "list_workshop_sources": {
        "purpose": "List slide/document sources used by the AI tutor.",
        "inputs": ["cohort", "workshopNo", "status"],
        "outputs": ["sources"],
    },
    "list_tools": {
        "purpose": "List available LMS AI Learning Assistant tools.",
        "inputs": [],
        "outputs": ["tools"],
    },
}


def retrieve_slide_sources_impl(
    question: str = "",
    cohort: str | None = None,
    workshopNo: int | None = None,
    topK: int = 3,
    workshop_no: int | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    resolved_workshop_no = workshopNo if workshopNo is not None else workshop_no
    resolved_top_k = topK if top_k is None else top_k
    sources = _load_sources(status="published")
    ranked = _rank_sources(
        question=question,
        sources=sources,
        cohort=cohort,
        workshop_no=resolved_workshop_no,
    )
    return {
        "tool": "retrieve_slide_sources",
        "question": question,
        "matches": [
            _match_payload(source=item["source"], score=item["score"])
            for item in ranked[: max(1, int(resolved_top_k or 3))]
        ],
    }


def classify_question_scope_impl(
    question: str = "",
    retrievedMatches: list[dict[str, Any]] | None = None,
    retrieved_matches: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    matches = retrievedMatches if retrievedMatches is not None else retrieved_matches
    matches = matches or []
    best_score = max((_as_float(match.get("score")) for match in matches), default=0.0)

    if _has_out_of_scope_terms(question):
        return {
            "tool": "classify_question_scope",
            "scope": "out_of_scope",
            "reason": "Cau hoi xin tu van ngoai pham vi hoc lieu workshop chinh thuc.",
            "confidence": 0.0,
        }

    if best_score >= IN_SCOPE_THRESHOLD:
        return {
            "tool": "classify_question_scope",
            "scope": "in_scope",
            "reason": "Tim thay nguon chinh thuc phu hop voi cau hoi.",
            "confidence": round(best_score, 2),
        }
    if best_score >= LOW_CONFIDENCE_THRESHOLD:
        return {
            "tool": "classify_question_scope",
            "scope": "low_confidence",
            "reason": "Co nguon gan dung nhung diem match chua du de tra loi tu tin.",
            "confidence": round(best_score, 2),
        }
    return {
        "tool": "classify_question_scope",
        "scope": "out_of_scope",
        "reason": "Khong tim thay slide hoac nguon chinh thuc du phu hop.",
        "confidence": round(best_score, 2),
    }


def generate_grounded_answer_impl(
    question: str = "",
    sources: list[dict[str, Any]] | None = None,
    studentLevel: str = "beginner",
    language: str = "vi",
    student_level: str | None = None,
) -> dict[str, Any]:
    selected_sources = sources or []
    if not selected_sources:
        return {
            "tool": "generate_grounded_answer",
            "answer": "",
            "example": "",
            "citations": [],
            "error": "No sources provided. Use handle_low_confidence_answer instead.",
        }

    primary = selected_sources[0]
    summary = _clean(primary.get("summary"))
    excerpt = _clean(primary.get("sourceExcerpt") or primary.get("source_excerpt"))
    section_title = _clean(primary.get("sectionTitle") or primary.get("section_title"))
    resolved_level = student_level or studentLevel

    if language == "en":
        answer = (
            f"{section_title}: {summary} "
            "This answer is based only on the retrieved workshop source."
        )
        example = _english_example(section_title, excerpt, resolved_level)
    else:
        answer = (
            f"{section_title}: {summary} "
            "Cau tra loi nay chi dua tren nguon workshop da truy xuat."
        )
        example = _vietnamese_example(section_title, excerpt, resolved_level)

    return {
        "tool": "generate_grounded_answer",
        "answer": answer,
        "example": example,
        "citations": [
            {
                "sourceId": source.get("sourceId") or source.get("source_id"),
                "citationLabel": source.get("citationLabel") or source.get("citation_label"),
                "excerpt": source.get("sourceExcerpt") or source.get("source_excerpt"),
            }
            for source in selected_sources
        ],
    }


def handle_low_confidence_answer_impl(
    question: str = "",
    reason: str = "",
    closestSources: list[dict[str, Any]] | None = None,
    closest_sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    closest = closestSources if closestSources is not None else closest_sources
    if _has_out_of_scope_terms(question):
        suggestions = _default_suggested_questions()
    else:
        suggestions = _suggested_questions(closest or [])
    return {
        "tool": "handle_low_confidence_answer",
        "message": (
            "Minh chua tim thay noi dung nay trong tai lieu chinh thuc cua workshop. "
            f"Ly do: {reason or 'nguon truy xuat chua du tin cay'}. "
            "Ban co the hoi cu the hon trong pham vi bai hoc."
        ),
        "suggestedQuestions": suggestions,
    }


def submit_answer_feedback_impl(
    question: str = "",
    sourceIds: list[str] | None = None,
    feedbackType: str = "unclear_answer",
    userRole: str = "student",
    answerId: str | None = None,
    note: str | None = None,
    source_ids: list[str] | None = None,
    feedback_type: str | None = None,
    user_role: str | None = None,
    answer_id: str | None = None,
    storage_path: str | None = None,
) -> dict[str, Any]:
    resolved_source_ids = sourceIds if sourceIds is not None else source_ids
    resolved_feedback_type = feedback_type or feedbackType
    resolved_user_role = user_role or userRole
    resolved_answer_id = answer_id or answerId
    feedback_id = _feedback_id(question, resolved_source_ids or [], resolved_feedback_type, note)
    next_action = _next_feedback_action(resolved_feedback_type, resolved_user_role)
    record = {
        "feedbackId": feedback_id,
        "question": question,
        "answerId": resolved_answer_id,
        "sourceIds": resolved_source_ids or [],
        "feedbackType": resolved_feedback_type,
        "note": note,
        "userRole": resolved_user_role,
        "nextAction": next_action,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    path = Path(storage_path) if storage_path else FEEDBACK_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {
        "tool": "submit_answer_feedback",
        "saved": True,
        "feedbackId": feedback_id,
        "nextAction": next_action,
    }


def list_workshop_sources_impl(
    cohort: str | None = None,
    workshopNo: int | None = None,
    status: str | None = None,
    workshop_no: int | None = None,
) -> dict[str, Any]:
    resolved_workshop_no = workshopNo if workshopNo is not None else workshop_no
    sources = _load_sources(status=status)
    rows = []
    for source in sources:
        if cohort and fold_text(source.get("cohort", "")) != fold_text(cohort):
            continue
        if resolved_workshop_no is not None and _source_workshop_no(source) != resolved_workshop_no:
            continue
        rows.append(
            {
                "sourceId": source.get("source_id"),
                "workshopTitle": source.get("workshop_title") or _day_title(source),
                "slideNo": source.get("slide_no"),
                "sectionTitle": source.get("section_title"),
                "status": source.get("status"),
                "citationLabel": source.get("citation_label"),
            }
        )
    rows.sort(key=lambda row: (row.get("workshopTitle") or "", row.get("slideNo") or 0))
    return {"tool": "list_workshop_sources", "sources": rows}


def list_tools_impl() -> dict[str, Any]:
    return {
        "tool": "list_tools",
        "tools": [
            {"name": name, **metadata}
            for name, metadata in TOOL_DESCRIPTIONS.items()
        ],
    }


def _load_sources(status: str | None = None) -> list[dict[str, Any]]:
    records_by_id: dict[str, dict[str, Any]] = {}
    for path in SOURCE_PATHS:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for record in payload.get("records", []):
            source_id = record.get("source_id")
            if not source_id:
                continue
            if status and record.get("status") != status:
                continue
            records_by_id.setdefault(source_id, record)
    return list(records_by_id.values())


def _rank_sources(
    question: str,
    sources: list[dict[str, Any]],
    cohort: str | None,
    workshop_no: int | None,
) -> list[dict[str, Any]]:
    query_terms = terms(question)
    ranked = []
    for source in sources:
        if cohort and fold_text(source.get("cohort", "")) != fold_text(cohort):
            continue
        if workshop_no is not None and _source_workshop_no(source) != workshop_no:
            continue

        raw_score = 0
        for field, weight in FIELD_WEIGHTS.items():
            overlap = query_terms & terms(_field_text(source.get(field)))
            raw_score += len(overlap) * weight

        exact_text = fold_text(" ".join(_field_text(source.get(field)) for field in FIELD_WEIGHTS))
        folded_question = fold_text(question).strip()
        if folded_question and folded_question in exact_text:
            raw_score += 12
        if folded_question and any(
            folded_question == fold_text(example)
            for example in source.get("example_student_questions", [])
        ):
            raw_score += 24
        if folded_question and folded_question in fold_text(source.get("section_title", "")):
            raw_score += 10
        if workshop_no is not None:
            raw_score += 2

        if raw_score:
            ranked.append(
                {
                    "source": source,
                    "score": min(1.0, raw_score / 30),
                    "rank_score": raw_score,
                }
            )

    ranked.sort(key=lambda item: item["rank_score"], reverse=True)
    return ranked


def _match_payload(source: dict[str, Any], score: float) -> dict[str, Any]:
    return {
        "sourceId": source.get("source_id"),
        "score": round(score, 2),
        "citationLabel": source.get("citation_label"),
        "sourceExcerpt": source.get("source_excerpt"),
        "summary": source.get("summary"),
        "slideNo": source.get("slide_no"),
        "sectionTitle": source.get("section_title"),
    }


def _field_text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return "" if value is None else str(value)


def _source_workshop_no(source: dict[str, Any]) -> int | None:
    value = source.get("workshop_no")
    if value is None:
        value = source.get("day")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _day_title(source: dict[str, Any]) -> str:
    day = source.get("day")
    if day:
        return f"Day {day}"
    return "Workshop source"


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def _vietnamese_example(section_title: str, excerpt: str, student_level: str) -> str:
    prefix = "Vi du don gian" if student_level == "beginner" else "Vi du ap dung"
    return f"{prefix}: voi chu de '{section_title}', hay bam vao y chinh: {excerpt}"


def _english_example(section_title: str, excerpt: str, student_level: str) -> str:
    prefix = "Simple example" if student_level == "beginner" else "Applied example"
    return f"{prefix}: for '{section_title}', focus on this source idea: {excerpt}"


def _suggested_questions(closest_sources: list[dict[str, Any]]) -> list[str]:
    suggestions = []
    for source in closest_sources[:3]:
        title = source.get("sectionTitle") or source.get("section_title") or source.get("citationLabel")
        if title:
            folded_title = fold_text(title).strip()
            if folded_title.endswith(" la gi"):
                suggestions.append(str(title))
            else:
                suggestions.append(f"{title} la gi?")
    if suggestions:
        return suggestions
    return _default_suggested_questions()


def _default_suggested_questions() -> list[str]:
    return [
        "Chunking trong RAG la gi?",
        "Chunk qua dai anh huong retrieval the nao?",
        "Metadata giup retrieval tot hon ra sao?",
    ]


def _has_out_of_scope_terms(question: str) -> bool:
    folded = fold_text(question)
    return any(term in folded for term in OUT_OF_SCOPE_TERMS)


def _next_feedback_action(feedback_type: str, user_role: str) -> str:
    if feedback_type == "helpful":
        return "no_action"
    if user_role in {"mentor", "admin"} or feedback_type in {"wrong_citation", "wrong_answer"}:
        return "add_to_golden_test"
    return "mentor_review"


def _feedback_id(
    question: str,
    source_ids: list[str],
    feedback_type: str,
    note: str | None,
) -> str:
    raw = "|".join([question, ",".join(source_ids), feedback_type, note or ""])
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"FB-{digest}"
