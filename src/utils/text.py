"""Lightweight text normalization for research preprocessing and QA matching."""

from __future__ import annotations

import re
import unicodedata


_WS = re.compile(r"\s+")
_MOJIBAKE_MARKERS = (
    "Ã",
    "Â",
    "Ä",
    "Å",
    "áº",
    "á»",
    "ðŸ",
    "�",
)


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


def detect_mojibake(text: str) -> dict[str, object]:
    """Heuristic mojibake detector for UTF-8/console corruption in test inputs."""
    s = str(text or "")
    reasons: list[str] = []

    if any(marker in s for marker in _MOJIBAKE_MARKERS):
        reasons.append("mojibake_marker_sequence_detected")

    # Typical replacement-character corruption: letters separated by '?' in-word.
    if re.search(r"[A-Za-z]\?[A-Za-z]", s):
        reasons.append("replacement_question_mark_in_word")

    q_count = s.count("?")
    alpha_count = len(re.findall(r"[A-Za-z]", s))
    if q_count >= 3 and alpha_count > 0 and (q_count / max(alpha_count, 1)) > 0.05:
        reasons.append("suspicious_question_mark_density")

    return {
        "is_mojibake": bool(reasons),
        "reasons": reasons,
        "question_mark_count": q_count,
    }


def assert_clean_unicode_input(text: str, *, where: str = "") -> None:
    diag = detect_mojibake(text)
    if not bool(diag.get("is_mojibake")):
        return
    tag = f"[{where}] " if where else ""
    raise ValueError(
        f"{tag}Input appears mojibake/corrupted; fix encoding before parser quality assertions. "
        f"details={diag}"
    )
