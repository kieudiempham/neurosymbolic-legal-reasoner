"""Typed clarification targets (v5) — kind, expected answer type, priority."""

from __future__ import annotations

import re
from typing import Any

# target_kind values (API-stable strings)
MISSING_FACT = "missing_fact"
MISSING_NUMERIC_INPUT = "missing_numeric_input"
MISSING_TIME_INPUT = "missing_time_input"
MISSING_EXCEPTION_CHECK = "missing_exception_check"
MISSING_DOCUMENT_INPUT = "missing_document_input"
MISSING_CONSTRAINT_INPUT = "missing_constraint_input"
AMBIGUOUS_SUBJECT_OR_CONDITION = "ambiguous_subject_or_condition"


def infer_target_kind(fact_key: str, requirement_kind: str | None) -> str:
    fk = fact_key.strip()
    low = fk.lower()
    rk = (requirement_kind or "").lower()
    if low.startswith("parse_amb:"):
        return AMBIGUOUS_SUBJECT_OR_CONDITION
    if rk == "exception" or "exception_applies(" in low or low.startswith("unless("):
        return MISSING_EXCEPTION_CHECK
    if rk == "constraint" or "constraint:" in low:
        if "threshold" in low or "nguong" in low or "percent" in low:
            return MISSING_NUMERIC_INPUT
        if "deadline" in low or "thoi_han" in low or "time" in low:
            return MISSING_TIME_INPUT
        if "dossier" in low or "ho_so" in low or "document" in low:
            return MISSING_DOCUMENT_INPUT
        return MISSING_CONSTRAINT_INPUT
    if rk == "negative":
        return MISSING_EXCEPTION_CHECK
    return MISSING_FACT


def expected_answer_type(target_kind: str) -> str:
    return {
        MISSING_FACT: "yes_no",
        MISSING_NUMERIC_INPUT: "number",
        MISSING_TIME_INPUT: "date",
        MISSING_EXCEPTION_CHECK: "yes_no",
        MISSING_DOCUMENT_INPUT: "short_text",
        MISSING_CONSTRAINT_INPUT: "short_text",
        AMBIGUOUS_SUBJECT_OR_CONDITION: "choice",
    }.get(target_kind, "short_text")


def priority_for_kind(target_kind: str, *, is_blocking_parse: bool = False) -> int:
    """Lower = ask sooner (more blocking / applicability first)."""
    if is_blocking_parse:
        return 2
    base = {
        MISSING_EXCEPTION_CHECK: 5,
        MISSING_TIME_INPUT: 8,
        MISSING_NUMERIC_INPUT: 10,
        MISSING_DOCUMENT_INPUT: 12,
        MISSING_CONSTRAINT_INPUT: 14,
        MISSING_FACT: 18,
        AMBIGUOUS_SUBJECT_OR_CONDITION: 6,
    }
    return base.get(target_kind, 20)


def clarification_question_for_kind(
    target_kind: str,
    fact_key: str,
    *,
    requirement_kind: str | None = None,
    fallback_text: str = "",
) -> str:
    """User-facing question by kind (Vietnamese templates)."""
    fk = fact_key.strip()
    if fk.startswith("applies_if("):
        inner = fk[len("applies_if(") : -1]
        return f"Điều kiện áp dụng sau có đúng với tình huống của bạn không: {inner} ?"
    if fk.startswith("applies_to("):
        inner = fk[len("applies_to(") : -1]
        return f"Phạm vi áp dụng sau có đúng không: {inner} ?"
    if fallback_text and target_kind == MISSING_FACT and len(fk) < 3:
        return fallback_text

    if target_kind == MISSING_NUMERIC_INPUT:
        return (
            "Vui lòng cho biết giá trị định lượng liên quan (ví dụ tỷ lệ %, số lao động, mức vốn) "
            f"theo yêu cầu: {fk}"
        )
    if target_kind == MISSING_TIME_INPUT:
        return (
            "Thời điểm hoặc thời hạn cần áp dụng là gì (ngày cụ thể hoặc số ngày)? "
            f"Liên quan: {fk}"
        )
    if target_kind == MISSING_EXCEPTION_CHECK:
        if "exception_applies(" in fk:
            inner = fk[len("exception_applies(") : -1] if fk.endswith(")") else fk
            return f"Trường hợp của bạn có thuộc ngoại lệ sau không: {inner} ?"
        return f"Ngoại lệ sau có áp dụng với tình huống của bạn không? ({fk})"
    if target_kind == MISSING_DOCUMENT_INPUT:
        return (
            "Doanh nghiệp hiện đã có tài liệu / hồ sơ nào trong các mục sau? "
            f"Vui lòng mô tả ngắn gọn. ({fk})"
        )
    if target_kind == MISSING_CONSTRAINT_INPUT:
        return f"Vui lòng bổ sung thông tin để kiểm tra ràng buộc kỹ thuật: {fk}"
    if target_kind == AMBIGUOUS_SUBJECT_OR_CONDITION:
        return fallback_text or f"Làm rõ thông tin: {fk}"
    # missing_fact — reuse specific atoms from clarification_manager patterns via import cycle avoid:
    if "thay_doi_nguoi_dai_dien" in fk or "change_legal_representative" in fk:
        return "Doanh nghiệp của bạn có đang (hoặc sẽ) thay đổi người đại diện theo pháp luật không?"
    return f"Vui lòng xác nhận thông tin liên quan tới: {fk}"


def _constraint_parts(fact_key: str) -> tuple[str, str, str, str]:
    """Parse `constraint:<type>:<metric>:<operator>:<value>:<unit>` style keys safely."""
    low = fact_key.strip().lower()
    if not low.startswith("constraint:"):
        return "", "", "", ""
    rest = low[len("constraint:") :]
    parts = (rest.split(":") + ["", "", "", "", ""])[:5]
    ctype = parts[0]
    metric = parts[1]
    op = parts[2]
    val = parts[3]
    unit = parts[4]
    return ctype, metric, op, f"{val}:{unit}".strip(":")


def materialize_clarification_target(
    fact_key: str,
    *,
    requirement_kind: str | None = None,
    fallback_text: str = "",
) -> dict[str, Any]:
    """
    Convert internal/placeholder requirement keys to user-grounded clarification targets.

    Returns dict with keys:
      - fact_key: user-facing key
      - source_fact_key: internal key used by reasoner
      - target_kind / expected_type / question_text / options / is_placeholder
    """
    src = str(fact_key or "").strip()
    low = src.lower()
    rk = (requirement_kind or "").strip().lower()

    # Default behavior keeps existing key.
    kind = infer_target_kind(src, requirement_kind)
    out: dict[str, Any] = {
        "fact_key": src,
        "source_fact_key": src,
        "target_kind": kind,
        "expected_type": expected_answer_type(kind),
        "question_text": clarification_question_for_kind(kind, src, requirement_kind=requirement_kind, fallback_text=fallback_text),
        "options": [],
        "is_placeholder": False,
    }

    if low in {"condition()", "condition"}:
        out.update(
            {
                "fact_key": "legal_ground",
                "target_kind": MISSING_CONSTRAINT_INPUT,
                "expected_type": "short_text",
                "question_text": "Anh/chị có thể mô tả rõ căn cứ pháp lý hoặc bối cảnh áp dụng mà mình đang hỏi không?",
                "is_placeholder": True,
            }
        )
        return out

    ctype, metric, _op, value_unit = _constraint_parts(src)
    if ctype == "deadline":
        # `constraint:deadline:X` and similar should become concrete temporal targets.
        if any(x in low for x in ("bao_lau", "thoi_gian", "thu_viec", "toi_da")):
            out.update(
                {
                    "fact_key": "duration_limit",
                    "target_kind": MISSING_TIME_INPUT,
                    "expected_type": "duration",
                    "question_text": "Anh/chị muốn hỏi mốc thời lượng cụ thể là bao nhiêu ngày/tháng?",
                    "is_placeholder": True,
                }
            )
        elif "x" in low or not value_unit:
            out.update(
                {
                    "fact_key": "deadline_anchor_event",
                    "target_kind": MISSING_TIME_INPUT,
                    "expected_type": "short_text",
                    "question_text": "Anh/chị muốn tính thời hạn kể từ sự kiện nào (ví dụ: ngày ký, ngày thông báo, ngày chấm dứt)?",
                    "is_placeholder": True,
                }
            )
        else:
            out.update(
                {
                    "fact_key": "deadline_date",
                    "target_kind": MISSING_TIME_INPUT,
                    "expected_type": "date",
                    "question_text": "Anh/chị có thể cung cấp ngày/mốc thời gian cụ thể để áp dụng quy định không?",
                    "is_placeholder": True,
                }
            )
        return out

    if ctype == "threshold":
        if any(x in metric for x in ("thoi_gian", "thu_viec", "duration")):
            out.update(
                {
                    "fact_key": "duration_limit",
                    "target_kind": MISSING_NUMERIC_INPUT,
                    "expected_type": "duration",
                    "question_text": "Anh/chị muốn ngưỡng thời lượng tối đa là bao nhiêu ngày/tháng?",
                    "is_placeholder": True,
                }
            )
            return out
        if any(x in low for x in ("luong", "salary", "toi_thieu")):
            out.update(
                {
                    "fact_key": "salary_minimum_basis",
                    "target_kind": MISSING_NUMERIC_INPUT,
                    "expected_type": "choice",
                    "options": ["luong_toi_thieu_vung", "luong_hop_dong", "muc_luong_thoa_thuan"],
                    "question_text": "Anh/chị muốn lấy căn cứ mức lương tối thiểu theo phương án nào?",
                    "is_placeholder": True,
                }
            )
            return out
        out.update(
            {
                "fact_key": "threshold_value",
                "target_kind": MISSING_NUMERIC_INPUT,
                "expected_type": "number",
                "question_text": "Anh/chị vui lòng cung cấp giá trị ngưỡng cụ thể (số) để hệ thống kiểm tra điều kiện.",
                "is_placeholder": True,
            }
        )
        return out

    if ctype == "dossier":
        out.update(
            {
                "fact_key": "legal_ground",
                "target_kind": MISSING_DOCUMENT_INPUT,
                "expected_type": "short_text",
                "question_text": "Anh/chị đang nói tới bộ hồ sơ/tài liệu cụ thể nào?",
                "is_placeholder": True,
            }
        )
        return out

    # Non-constraint placeholders: keep semantic keys but avoid internal jargon in question text.
    if src.endswith("()") and re.match(r"^[a-z_]+\(\)$", low):
        out.update(
            {
                "fact_key": "legal_ground",
                "target_kind": MISSING_CONSTRAINT_INPUT,
                "expected_type": "short_text",
                "question_text": "Anh/chị có thể nêu rõ bối cảnh pháp lý cụ thể của trường hợp này không?",
                "is_placeholder": True,
            }
        )
        return out

    if rk == "constraint" and ("constraint:" in low):
        out.update(
            {
                "fact_key": "legal_ground",
                "target_kind": MISSING_CONSTRAINT_INPUT,
                "expected_type": "short_text",
                "question_text": "Anh/chị vui lòng bổ sung thông tin pháp lý cốt lõi để hệ thống áp dụng đúng ràng buộc.",
                "is_placeholder": True,
            }
        )
    return out


def merge_priority(parse_priority: int, backward_priority: int) -> int:
    return min(parse_priority, backward_priority)
