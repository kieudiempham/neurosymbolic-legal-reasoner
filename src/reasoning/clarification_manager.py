"""Generate clarification questions for missing symbolic requirements."""

from __future__ import annotations


def clarification_for_missing_fact(fact_key: str) -> str:
    fk = fact_key.strip()
    if "change_legal_representative" in fk:
        return "Công ty của bạn có đang (hoặc sẽ) thay đổi người đại diện theo pháp luật không?"
    if fk.startswith("applies_if("):
        inner = fk[len("applies_if(") : -1]
        return f"Điều kiện áp dụng sau có đúng với tình huống của bạn không: {inner} ?"
    if fk.startswith("unless("):
        inner = fk[len("unless(") : -1]
        return f"Ngoại lệ sau có áp dụng không: {inner} ?"
    if fk.startswith("applies_to("):
        inner = fk[len("applies_to(") : -1]
        return f"Phạm vi áp dụng sau có đúng không: {inner} ?"
    return f"Vui lòng xác nhận thông tin liên quan tới: {fk}"


def build_clarification_prompts(missing_keys: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for k in missing_keys:
        out.append({"fact_key": k, "question_text": clarification_for_missing_fact(k)})
    return out
