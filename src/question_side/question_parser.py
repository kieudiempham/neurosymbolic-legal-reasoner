"""Layer 1 parse — heuristic / rule-based (research demo, not black-box)."""

from __future__ import annotations

import re

from schemas.question_parse import Layer1Parse, QuestionFocus, UtteranceType
from utils.text import lower_fold, normalize_ws


def parse_question_layer1(question: str) -> Layer1Parse:
    q = normalize_ws(question)
    low = lower_fold(q)

    utterance_type: UtteranceType = "question"
    modality_text = ""
    # `low` is accent-stripped (see lower_fold); match folded keywords only.
    if "co phai" in low or "phai " in low or "phai khong" in low:
        modality_text = "phải"
    if "duoc" in low and ("khong" in low or "hay khong" in low):
        modality_text = modality_text or "được_phải"

    question_focus: QuestionFocus = "unknown"
    if "co the" in low or "duoc phep" in low:
        question_focus = "permission"
    elif any(x in low for x in ("co phai dang ky", "phai dang ky", "dang ky thay doi")):
        question_focus = "obligation"
    elif "thoi han" in low or "trong vong" in low or " ngay " in low:
        question_focus = "deadline"
    elif "it nhat" in low or "%" in q or "phan tram" in low:
        question_focus = "threshold"
    elif "tru truong hop" in low or "ngoai le" in low:
        question_focus = "exception"

    subject_text = ""
    condition_text = ""
    action_text = ""
    exception_text = ""

    m = re.search(r"^(.*?)(?:thì|,)\s*(.+)$", q)
    if m:
        left = m.group(1).strip()
        right = m.group(2).strip()
        if "cong ty" in lower_fold(left) or "doanh nghiep" in lower_fold(left):
            subject_text = left
        condition_text = left
        action_text = right
    else:
        subject_text = q[: min(80, len(q))]
        action_text = q

    if "tru truong hop" in low or "ngoai le" in low:
        parts = re.split(r"(trừ|ngoại lệ)", q, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) >= 2:
            exception_text = normalize_ws(parts[-1])

    assertion_status = "hypothetical"
    if any(x in low for x in ("toi da", "chung toi da", "da dang ky")):
        assertion_status = "factual"

    notes: list[str] = ["heuristic_layer1_v1"]

    return Layer1Parse(
        utterance_type=utterance_type,
        subject_text=subject_text or q[:120],
        condition_text=condition_text,
        action_text=action_text,
        modality_text=modality_text,
        time_text="",
        exception_text=exception_text,
        question_focus=question_focus,
        assertion_status=assertion_status,
        raw_notes=notes,
    )
