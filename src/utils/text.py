"""Lightweight text normalization for research preprocessing and QA matching."""

from __future__ import annotations

import re
import unicodedata


_WS = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace."""
    return _WS.sub(" ", text).strip()


def truncate(text: str, max_chars: int) -> str:
    """Shorten text for logs; adds an ellipsis when the string is cut."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def strip_accents(s: str) -> str:
    s = s.replace("đ", "d").replace("Đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def lower_fold(s: str) -> str:
    """Lowercase + accent-fold for robust Vietnamese keyword matching."""
    return normalize_ws(strip_accents(s.lower()))


def slug_token(s: str) -> str:
    t = lower_fold(s)
    t = re.sub(r"[^a-z0-9]+", "_", t)
    return re.sub(r"_+", "_", t).strip("_") or "unknown"
