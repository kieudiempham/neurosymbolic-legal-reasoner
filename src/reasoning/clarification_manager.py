"""Generate clarification questions for missing symbolic requirements."""

from __future__ import annotations

from typing import Any

from reasoning.internal.codec import serialize_atom
from reasoning.internal.models import Atom
from reasoning.semantics.failed_path_hints import sort_clarification_keys_by_failed_paths
from reasoning.semantics.plan_models import FailedPathRecord
from schemas.reasoning import RequirementItem


def clarification_for_missing_fact(fact_key: str, requirement_kind: str | None = None) -> str:
    fk = fact_key.strip()
    if requirement_kind == "constraint" or fk.startswith("constraint:"):
        if "threshold" in fk:
            return f"Vui lòng xác nhận hoặc bổ sung thông tin liên quan ngưỡng / định lượng sau: {fk}"
        if "deadline" in fk:
            return f"Vui lòng xác nhận thông tin liên quan thời hạn / mốc thời gian: {fk}"
        if "dossier" in fk:
            return f"Vui lòng xác nhận hồ sơ / tài liệu liên quan: {fk}"
        return f"Vui lòng xác nhận ràng buộc kỹ thuật sau: {fk}"
    if requirement_kind == "exception" or fk.startswith("exception_applies("):
        inner = fk[len("exception_applies(") : -1] if fk.endswith(")") else fk
        return f"Ngoại lệ sau có áp dụng với tình huống của bạn không: {inner} ?"
    if requirement_kind == "negative" or fk.startswith("unless("):
        inner = fk[len("unless(") : -1] if fk.endswith(")") else fk
        return f"Ngoại lệ sau có áp dụng không: {inner} ?"
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


def _questions_from_backward_plan(backward_plan: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    cands = backward_plan.get("candidates") or []
    if not cands:
        return out
    c0 = cands[0]
    for m in c0.get("missing_atoms") or []:
        atom_d = m.get("atom") or {}
        try:
            a = Atom(predicate=str(atom_d.get("predicate", "")), args=tuple(atom_d.get("args") or []))
            k = serialize_atom(a)
        except Exception:
            k = ""
        q = m.get("question") or ""
        if k and q:
            out[k] = q
    for m in c0.get("missing_exception_inputs") or []:
        atom_d = m.get("atom") or {}
        try:
            a = Atom(predicate=str(atom_d.get("predicate", "")), args=tuple(atom_d.get("args") or []))
            k = serialize_atom(a)
        except Exception:
            k = ""
        q = m.get("question") or ""
        if k and q:
            out[k] = q
    for m in c0.get("missing_constraint_inputs") or []:
        sk = m.get("session_key_hint") or m.get("target") or ""
        q = m.get("question") or ""
        if sk and q:
            out[str(sk)] = q
    return out


def best_forward_failure_hint(forward_result: dict[str, Any] | None) -> str:
    """Chọn hint từ failed path có clarification_priority thấp nhất (cần hỏi / làm rõ sớm hơn)."""
    if not forward_result:
        return ""
    raw = forward_result.get("failed_path_records") or []
    if not raw:
        return ""
    recs = [FailedPathRecord.model_validate(x) for x in raw if x]
    if not recs:
        return ""
    best = min(recs, key=lambda r: r.clarification_priority)
    return best.user_message_hint or ""


def build_clarification_prompts(missing_keys: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for k in missing_keys:
        out.append({"fact_key": k, "question_text": clarification_for_missing_fact(k)})
    return out


def build_clarification_prompts_from_requirements(
    missing_keys: list[str],
    requirement_set: list[RequirementItem],
    backward_plan: dict[str, Any] | None = None,
    forward_result: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Dùng `requirement_kind` / atom khi có; ưu tiên câu hỏi chi tiết từ `backward_plan`; sắp xếp key theo `failed_path_records` nếu có."""
    keys = list(missing_keys)
    if forward_result:
        raw = forward_result.get("failed_path_records") or []
        recs = [FailedPathRecord.model_validate(x) for x in raw if x]
        keys = sort_clarification_keys_by_failed_paths(keys, recs)
    by_key = {r.key: r for r in requirement_set}
    plan_q = _questions_from_backward_plan(backward_plan) if backward_plan else {}
    hint = best_forward_failure_hint(forward_result)
    out: list[dict[str, str]] = []
    for k in keys:
        if k in plan_q and plan_q[k]:
            row: dict[str, str] = {"fact_key": k, "question_text": plan_q[k]}
            if hint:
                row["reason_hint"] = hint
            out.append(row)
            continue
        ri = by_key.get(k)
        kind = ri.requirement_kind if ri else None
        text = clarification_for_missing_fact(k, kind)
        row: dict[str, str] = {"fact_key": k, "question_text": text}
        if hint:
            row["reason_hint"] = hint
        out.append(row)
    return out
