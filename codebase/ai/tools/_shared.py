from __future__ import annotations

import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def fold_text(text: str) -> str:
    text = (text or "").replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def terms(text: str) -> set[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "anh",
        "are",
        "as",
        "at",
        "ban",
        "by",
        "can",
        "cho",
        "co",
        "cua",
        "duoc",
        "em",
        "for",
        "from",
        "gi",
        "in",
        "is",
        "khi",
        "la",
        "lam",
        "minh",
        "mot",
        "nao",
        "of",
        "on",
        "or",
        "the",
        "the",
        "theo",
        "thi",
        "to",
        "tom",
        "tat",
        "trong",
        "va",
        "ve",
        "voi",
        "sau",
        "doi",
        "app",
    }
    folded = fold_text(text)
    return {
        term
        for term in re.findall(r"[a-z0-9]+", folded)
        if len(term) > 1 and term not in stopwords
    }
