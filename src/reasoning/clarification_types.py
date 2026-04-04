"""Typed clarification targets (v5) — kind, expected answer type, priority."""

from __future__ import annotations

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
        MISSING_TIME_INPUT: "time",
        MISSING_EXCEPTION_CHECK: "yes_no",
        MISSING_DOCUMENT_INPUT: "document",
        MISSING_CONSTRAINT_INPUT: "text",
        AMBIGUOUS_SUBJECT_OR_CONDITION: "choice",
    }.get(target_kind, "text")


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


def merge_priority(parse_priority: int, backward_priority: int) -> int:
    return min(parse_priority, backward_priority)
