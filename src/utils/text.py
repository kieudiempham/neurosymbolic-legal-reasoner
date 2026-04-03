"""Lightweight text normalization for research preprocessing."""

from __future__ import annotations

import re


_WS = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace."""
    return _WS.sub(" ", text).strip()


def truncate(text: str, max_chars: int) -> str:
    """Shorten text for logs; adds an ellipsis when the string is cut."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."
