from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]


def err(tool: str, exc: Exception) -> dict[str, Any]:
    return {"tool": tool, "error": type(exc).__name__, "message": str(exc)}


def fold_text(text: str) -> str:
    text = (text or "").replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def terms(text: str) -> set[str]:
    stopwords = {
        "a", "an", "and", "anh", "are", "as", "at", "ban", "bao", "by",
        "can", "cho", "co", "cua", "duoc", "em", "for", "from", "gi", "giup",
        "in", "is", "khi", "la", "lam", "minh", "mot", "nao", "nay", "nen",
        "of", "on", "or", "the", "theo", "thi", "to", "tom", "tat",
        "trong", "va", "ve", "voi", "sau", "doi", "app",
    }
    folded = fold_text(text)
    return {
        term
        for term in re.findall(r"[a-z0-9]+", folded)
        if len(term) > 1 and term not in stopwords
    }
