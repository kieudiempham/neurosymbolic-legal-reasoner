"""Controlled, grounded query expansion for evidence retrieval (small alias map — no web RAG)."""

from __future__ import annotations

import re
from typing import Iterable

# Predicate / action tokens → extra Vietnamese cues (recall without large noise).
_LIGHT_ALIASES: dict[str, tuple[str, ...]] = {
    "obligation": ("nghĩa vụ", "bắt buộc", "phải thực hiện"),
    "permission": ("được phép", "có quyền", "có thể"),
    "prohibition": ("không được", "cấm", "nghiêm cấm"),
    "deadline": ("thời hạn", "trong vòng", "ngày"),
    "procedure": ("thủ tục", "trình tự", "hồ sơ"),
    "legal_consequence": ("hậu quả", "trách nhiệm", "xử lý"),
    "gui_phieu_lay_y_kien": ("phiếu lấy ý kiến", "lấy ý kiến"),
    "nop_ho_so": ("nộp hồ sơ", "hồ sơ đăng ký"),
    "thong_bao": ("thông báo", "báo cho"),
}

_TOKEN_SPLIT = re.compile(r"[\s,;|]+")


def aliases_for_predicate(pred: str | None) -> tuple[str, ...]:
    if not pred:
        return ()
    p = pred.strip().lower()
    if p in _LIGHT_ALIASES:
        return _LIGHT_ALIASES[p]
    return ()


def expand_query_terms(seed: str, *, goal_predicate: str | None = None, max_extra_tokens: int = 24) -> str:
    """Append alias phrases when seed mentions map keys or goal_predicate matches."""
    if not (seed or "").strip():
        return ""
    low = seed.lower()
    extras: list[str] = []
    extras.extend(aliases_for_predicate(goal_predicate))
    for key, aliases in _LIGHT_ALIASES.items():
        if key in low:
            extras.extend(aliases)
    # De-dup while preserving order
    seen: set[str] = set()
    out: list[str] = [seed.strip()]
    for x in extras:
        t = x.strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
        if len(seen) >= max_extra_tokens:
            break
    return " ".join(out)


def merge_query_variants(variants: Iterable[str]) -> list[str]:
    """Deduplicate non-empty query strings."""
    seen: set[str] = set()
    out: list[str] = []
    for v in variants:
        s = (v or "").strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out
