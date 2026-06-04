from __future__ import annotations

from typing import Any

from .classify_question_scope.tool import classify_question_scope
from .explain.tool import explain
from .generate_grounded_answer.tool import generate_grounded_answer
from .handle_low_confidence_answer.tool import handle_low_confidence_answer
from .list_tools.tool import list_tools
from .list_workshop_sources.tool import list_workshop_sources
from .retrieve_slide_sources.tool import retrieve_slide_sources
from .submit_answer_feedback.tool import submit_answer_feedback
from .summarize.tool import summarize


TOOL_FUNCTIONS: dict[str, Any] = {
    "classify_question_scope": classify_question_scope,
    "explain": explain,
    "generate_grounded_answer": generate_grounded_answer,
    "handle_low_confidence_answer": handle_low_confidence_answer,
    "list_tools": list_tools,
    "list_workshop_sources": list_workshop_sources,
    "retrieve_slide_sources": retrieve_slide_sources,
    "submit_answer_feedback": submit_answer_feedback,
    "summarize": summarize,
}
