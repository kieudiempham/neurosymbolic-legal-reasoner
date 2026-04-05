"""Heuristic Layer-1 parser (fallback / benchmark) — no LLM."""

from __future__ import annotations

import re

from schemas.question_parse import AssertionStatus, Layer1Parse, QuestionFocus, UtteranceType
from utils.text import lower_fold, normalize_ws

# Permission-style "được" without overlapping "có được quyền / bằng / bổ nhiệm" regression cases.
_RE_CO_DUOC_GUI = re.compile(r"\bcó được\s+gửi\b", re.IGNORECASE)


def parse_question_layer1_heuristic(question: str) -> Layer1Parse:
    q = normalize_ws(question)
    low = lower_fold(q)

    # Utterance type (v5-oriented)
    utterance_type: UtteranceType = "direct_question"
    if re.search(r"\bnếu\b|\bneu\b", low) or "trong truong hop" in low or "trong trường hợp" in q.lower():
        utterance_type = "conditional_legal_question"
    if "gia su" in low or "giả sử" in q.lower() or re.search(r"\bneu\s+.*\s+thi\b", low):
        utterance_type = "hypothetical_question"
    if utterance_type == "direct_question" and (
        low.count("hay") > 1 or ("co the" in low and "hay la" in low)
    ):
        utterance_type = "ambiguous_question"

    modality_text = ""
    if any(x in low for x in ("khong duoc", "cấm", "cam", "bi cam")):
        modality_text = "không được"
    elif "co quyen" in low or "có quyền" in q.lower():
        modality_text = "có quyền"
    elif _RE_CO_DUOC_GUI.search(q) or "co duoc gui" in low:
        modality_text = "được"
    elif "duoc phep" in low or "được phép" in q.lower() or ("co the" in low and "duoc" in low):
        modality_text = "được"
    elif any(x in low for x in ("co phai", "phai khong", "bat buoc", "nghia vu")):
        modality_text = "phải"
    elif "co phai" in low or "phải không" in q.lower():
        modality_text = "có phải ... không"

    question_focus: QuestionFocus = "unknown"
    if modality_text in ("không được",) or "cấm" in q.lower():
        question_focus = "prohibition"
    elif _RE_CO_DUOC_GUI.search(q) or "co duoc gui" in low or "co the" in low or "duoc phep" in low or "được phép" in q.lower():
        question_focus = "permission"
    elif "thu tuc" in low or "thủ tục" in q.lower():
        question_focus = "procedure"
    elif any(x in low for x in ("co phai dang ky", "phai dang ky", "dang ky thay doi")):
        question_focus = "obligation"
    elif "hau qua" in low or "chịu trách" in q.lower() or "trach nhiem phap ly" in low:
        question_focus = "legal_consequence"
    elif any(x in low for x in ("co phai", "phai ", "bat buoc", "nghia vu")):
        question_focus = "obligation"
    elif any(x in low for x in ("thoi han", "trong vong", " trong ", "han nop", "khi nao", "bao lau")):
        question_focus = "deadline"
    elif "it nhat" in low or "%" in q or "phan tram" in low:
        question_focus = "threshold"
    elif any(x in low for x in ("tru truong hop", "ngoai le", "ngoại trừ", "tru khi", "trừ khi")):
        question_focus = "exception"

    subject_text = ""
    condition_text = ""
    action_text = ""

    m_if = re.search(
        r"(?:nếu|neu|khi|trong trường hợp|trong truong hop)\s*(.+?)(?:\s+thì\s+|\s*,\s*)(.+)$",
        q,
        flags=re.IGNORECASE,
    )
    if m_if:
        condition_text = normalize_ws(m_if.group(1))
        rest = normalize_ws(m_if.group(2))
        if "công ty" in lower_fold(condition_text) or "doanh nghiệp" in lower_fold(condition_text):
            subject_text = condition_text[:120]
        else:
            subject_text = rest[:120]
        action_text = rest
    else:
        m = re.search(r"^(.*?)(?:thì|,)\s*(.+)$", q)
        if m:
            left = normalize_ws(m.group(1))
            right = normalize_ws(m.group(2))
            condition_text = left
            if "cong ty" in lower_fold(left) or "doanh nghiep" in lower_fold(left):
                subject_text = left
            else:
                subject_text = left[:80]
            action_text = right
        else:
            subject_text = q[: min(120, len(q))]
            action_text = q

    time_text = ""
    deadline_text = ""
    tm = re.search(
        r"(trong vòng|trong vo|trong thời hạn|trong thoi han|thời hạn|thoi han|trong\s+\d+[\s,]*ngày|"
        r"\d+\s*ngày|khi nào|bao lâu|hết hạn|het han|deadline)",
        q,
        flags=re.IGNORECASE,
    )
    if tm:
        span = tm.group(0)
        time_text = span
        deadline_text = span
    dm = re.search(r"(\d+[\s,.]*(?:ngày|tháng|năm|nam)\b[^?.]*)", q, flags=re.IGNORECASE)
    if dm and not deadline_text:
        deadline_text = normalize_ws(dm.group(1))

    exception_text = ""
    if any(x in low for x in ("tru truong hop", "ngoai le", "ngoại trừ", "tru khi", "trừ khi")):
        parts = re.split(r"(?:trừ trường hợp|ngoại lệ|ngoại trừ|trừ khi|ngoại trừ)", q, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) >= 2:
            exception_text = normalize_ws(parts[-1])

    assertion_status: AssertionStatus = "ambiguous"
    if any(x in low for x in ("toi da", "chung toi da", "đã đăng ký", "da dang ky", "thực tế", "thuc te")):
        assertion_status = "asserted"
    elif utterance_type in ("hypothetical_question", "conditional_legal_question"):
        assertion_status = "hypothetical"
    elif "gia su" in low or "giả sử" in q.lower():
        assertion_status = "hypothetical"

    notes = ["heuristic_layer1_v2"]

    meta = {
        "parser_backend": "heuristic",
        "parser_model": "",
        "fallback_used": False,
    }

    return Layer1Parse(
        utterance_type=utterance_type,
        subject_text=subject_text or q[:120],
        condition_text=condition_text,
        action_text=action_text,
        modality_text=modality_text,
        time_text=time_text,
        deadline_text=deadline_text,
        exception_text=exception_text,
        question_focus=question_focus,
        assertion_status=assertion_status,
        raw_notes=notes,
        parse_metadata=meta,
    )
