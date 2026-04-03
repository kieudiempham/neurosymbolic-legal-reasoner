"""Rule-based trigger lexicons and regex helpers.

This module contains *shared* heuristics between:
- normative sentence detection
- legal frame extraction

Keep patterns readable and easy to extend.
"""

from __future__ import annotations

import re
from typing import NamedTuple


class Trigger(NamedTuple):
    """A trigger pattern group used to classify normative sentences."""

    name: str
    regex: re.Pattern[str]


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, flags=re.IGNORECASE | re.UNICODE)


# ---- Modality triggers ----
OBLIGATION_TRIGGERS: list[Trigger] = [
    Trigger("obligation_phai", _compile(r"\bphải\b")),
    Trigger("obligation_co_nghia_vu", _compile(r"\bcó nghĩa vụ\b")),
    Trigger("obligation_chiu_trach_nhiem", _compile(r"\bchịu trách nhiệm\b")),
    Trigger("obligation_co_trach_nhiem", _compile(r"\bcó trách nhiệm\b")),
]

PROHIBITION_TRIGGERS: list[Trigger] = [
    Trigger("prohibition_khong_duoc", _compile(r"\bkhông được\b")),
    Trigger("prohibition_nghiem_cam", _compile(r"\bnghiêm cấm\b")),
]

PERMISSION_TRIGGERS: list[Trigger] = [
    Trigger("permission_duoc", _compile(r"\bđược\b")),
    Trigger("permission_co_quyen", _compile(r"\bcó quyền\b")),
    Trigger("permission_co_the", _compile(r"\bcó thể\b")),
]


# ---- Structural / legal cues ----
CONDITION_TRIGGERS: list[Trigger] = [
    Trigger("condition_nếu", _compile(r"\bnếu\b")),
    Trigger("condition_khi", _compile(r"\bkhi\b")),
    Trigger("condition_truong_hop", _compile(r"\btrường hợp\b")),
    Trigger("condition_doi_voi", _compile(r"\bđối với\b")),
    Trigger("condition_tru_truong_hop", _compile(r"\btrừ trường hợp\b")),
]

DEADLINE_TRIGGERS: list[Trigger] = [
    Trigger("deadline_trong_thoi_han", _compile(r"\btrong\s+(thời\s+hạn|vòng)\b")),
    Trigger("deadline_trong_vong", _compile(r"\btrong\s+vòng\b")),
    Trigger("deadline_ke_tu_ngay", _compile(r"\bkể từ ngày\b")),
    Trigger("deadline_cham_nhat", _compile(r"\bchậm nhất\b")),
]

DOSSIER_TRIGGERS: list[Trigger] = [
    Trigger("dossier_ho_so_bao_gom", _compile(r"\bhồ sơ bao gồm\b")),
    Trigger("dossier_kem_theo", _compile(r"\bkèm theo\b")),
    Trigger("dossier_bao_gom_giay_to", _compile(r"\bbao gồm các giấy tờ\b")),
    Trigger("dossier_bao_gom_tai_lieu", _compile(r"\bbao gồm các tài liệu\b")),
    Trigger("dossier_thong_bao_phai_bao_gom", _compile(r"\bthông báo\b.{0,40}\bphải bao gồm\b")),
]

AUTHORITY_TRIGGERS: list[Trigger] = [
    Trigger("authority_co_trach_nhiem_xem_xet", _compile(r"\bcó trách nhiệm xem xét\b")),
    Trigger("authority_cap", _compile(r"\bcấp\b")),
    Trigger("authority_tu_choi", _compile(r"\btừ chối\b")),
    Trigger("authority_thong_bao", _compile(r"\bthông báo\b")),
]


# ---- Frame type inference cues ----
STATUS_CUES: list[re.Pattern[str]] = [
    _compile(r"\bhết hiệu lực\b"),
    _compile(r"\bchấm dứt\b"),
    _compile(r"\bgia hạn\b"),
    _compile(r"\bđược cấp\b"),
    _compile(r"\bkhông còn\b"),
]


def classify_modality(text: str) -> str | None:
    """Return a coarse modality label for a Vietnamese sentence."""
    for trig in PROHIBITION_TRIGGERS:
        if trig.regex.search(text):
            return "prohibition"
    for trig in OBLIGATION_TRIGGERS:
        if trig.regex.search(text):
            return "obligation"
    for trig in PERMISSION_TRIGGERS:
        if trig.regex.search(text):
            return "permission"
    return None


def detect_candidate_categories(text: str) -> set[str]:
    """Return a set of normative categories present in the text."""
    cats: set[str] = set()
    if classify_modality(text) == "obligation":
        cats.add("duty")
    if classify_modality(text) == "prohibition":
        cats.add("prohibition")
    if classify_modality(text) == "permission":
        cats.add("permission")

    for trig in CONDITION_TRIGGERS:
        if trig.regex.search(text):
            cats.add("condition")
    for trig in DEADLINE_TRIGGERS:
        if trig.regex.search(text):
            cats.add("deadline")
    for trig in DOSSIER_TRIGGERS:
        if trig.regex.search(text):
            cats.add("document")
    for trig in AUTHORITY_TRIGGERS:
        if trig.regex.search(text):
            cats.add("authority")
    if any(p.search(text) for p in STATUS_CUES):
        cats.add("status")
    return cats


def find_trigger_span(text: str, trigger_patterns: list[Trigger]) -> tuple[str, int, int] | None:
    """Find the earliest trigger match and return (matched, start, end)."""
    best: tuple[str, int, int] | None = None
    for trig in trigger_patterns:
        m = trig.regex.search(text)
        if not m:
            continue
        span = (m.group(0), m.start(), m.end())
        if best is None or span[1] < best[1]:
            best = span
    return best


def extract_first_span_after_keyword(text: str, keyword_regex: re.Pattern[str], *, max_chars: int = 200) -> str | None:
    """Extract a coarse span after the first keyword occurrence."""
    m = keyword_regex.search(text)
    if not m:
        return None
    start = m.start()
    after = text[start : start + max_chars]
    # Stop at next sentence boundary if possible.
    stop = re.search(r"[.;]\s+", after)
    if stop:
        after = after[: stop.start()]
    return after.strip()

