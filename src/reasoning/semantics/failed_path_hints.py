"""User-facing hints and `FailedPathRecord` construction — no hard-coded final answers, reusable templates."""

from __future__ import annotations

from typing import Any

from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.semantics.plan_models import FailedPathRecord, FailureReason, ForwardPathResult
from schemas.rule import RuleRecord


def clarification_priority_for_failure(reason: FailureReason) -> int:
    """Lower = clarify sooner (missing input); higher = explain-only / blocked."""
    order: dict[str, int] = {
        "unknown_goal_atom": 6,
        "noncanonical_goal_surface": 7,
        "unknown_rule_head": 9,
        "constraint_schema_missing": 10,
        "weak_shared_template": 11,
        "predicate_family_mismatch": 14,
        "actor_role_mismatch": 16,
        "constraint_missing_input": 8,
        "unless_condition_unknown": 12,
        "positive_condition_missing": 18,
        "exception_unknown": 22,
        "constraint_unknown": 28,
        "constraint_failed": 55,
        "negative_condition_blocked": 82,
        "exception_triggered": 88,
        "unification_broken": 90,
        "goal_not_derived": 40,
        "none": 99,
    }
    return order.get(str(reason), 50)


def build_user_message_hint(res: ForwardPathResult, rule: RuleRecord | None = None) -> str:
    """Short Vietnamese hint for UI / explanation / next-step framing."""
    r = res.failure_reason
    detail = (res.failure_detail or "").strip()
    rid = res.rule_id or (rule.rule_id if rule else "")

    if r == "negative_condition_blocked":
        neg = res.blocking_negative_atoms[0] if res.blocking_negative_atoms else {}
        atom_s = neg.get("serialized") or detail
        return (
            f"Quy tắc {rid} không áp dụng vì điều kiện loại trừ (unless) đã xảy ra: {atom_s}. "
            "Đường suy luận này bị chặn."
        )
    if r == "unless_condition_unknown":
        return (
            f"Quy tắc {rid} chưa thể đánh giá hết: cần làm rõ điều kiện loại trừ (unless) "
            f"({detail or 'chưa có trong hồ sơ fact'})."
        )
    if r == "exception_triggered":
        return f"Quy tắc {rid} không áp dụng vì ngoại lệ đã được kích hoạt ({detail})."
    if r == "constraint_missing_input":
        return (
            f"Quy tắc {rid} chưa áp dụng được vì còn thiếu dữ liệu định lượng / ngưỡng "
            f"({detail or 'metric'}). Vui lòng bổ sung giá trị số theo metric tương ứng."
        )
    if r == "constraint_failed":
        return f"Quy tắc {rid} không thỏa điều kiện ngưỡng ({detail})."
    if r == "unknown_goal_atom":
        return f"Mục tiêu suy luận chưa canonical đủ để chạy forward ({detail or 'unknown_goal_atom'})."
    if r == "noncanonical_goal_surface":
        return f"Mục tiêu suy luận còn ở dạng surface-form, cần chuẩn hóa thêm trước khi chứng minh ({detail})."
    if r == "unknown_rule_head":
        return f"Quy tắc {rid} có head chưa usable cho forward ({detail})."
    if r == "predicate_family_mismatch":
        return f"Quy tắc {rid} lệch semantic family với goal nên bị chặn sớm ({detail})."
    if r == "actor_role_mismatch":
        return f"Quy tắc {rid} không khớp vai trò chủ thể với goal ({detail})."
    if r == "constraint_schema_missing":
        return f"Quy tắc {rid} thiếu schema ràng buộc cần thiết cho suy luận tiến ({detail})."
    if r == "weak_shared_template":
        return f"Shared rule {rid} chỉ là template yếu, không đủ chất lượng để sinh proof ({detail})."
    if r == "positive_condition_missing":
        return f"Quy tắc {rid} chưa áp dụng được vì còn thiếu điều kiện áp dụng ({detail})."
    if r == "exception_unknown":
        return f"Quy tắc {rid} cần làm rõ ngoại lệ có áp dụng hay không ({detail})."
    if r == "unification_broken":
        return f"Quy tắc {rid} không khớp mục tiêu suy luận (unify head thất bại)."
    return f"Quy tắc {rid} không cho kết luận ({r}): {detail}"


def failed_path_record_from_result(
    rule: RuleRecord,
    res: ForwardPathResult,
    *,
    goal: dict[str, Any],
) -> FailedPathRecord:
    """Map a failed forward run into a rich, user-facing record."""
    rr = map_rule_record_to_reasoning_rule(rule)
    prov = rule.metadata.get("provenance") or {}
    src = prov.get("source_ref")
    hint = build_user_message_hint(res, rule)
    pri = clarification_priority_for_failure(res.failure_reason)

    missing_atoms: list[dict[str, Any]] = []
    if res.failure_reason in ("positive_condition_missing", "unless_condition_unknown"):
        missing_atoms.append({"failure_detail": res.failure_detail, "goal": goal})

    missing_cons: list[str] = []
    if res.failure_reason == "constraint_missing_input" and res.failure_detail:
        missing_cons.append(res.failure_detail)

    failed_cons: list[dict[str, Any]] = []
    for t in res.constraint_traces:
        failed_cons.append(
            {
                "constraint_type": t.constraint_type,
                "status": t.status,
                "detail": t.detail,
                "session_key": t.session_key,
                "numeric_lookup": t.numeric_lookup,
            }
        )

    return FailedPathRecord(
        rule_id=rule.rule_id,
        goal_atom=list(res.goal_atom) if res.goal_atom else list(rr.goal_atom),
        failure_reason=res.failure_reason,
        failure_detail=res.failure_detail,
        missing_atoms=missing_atoms,
        missing_constraint_inputs=missing_cons,
        blocking_negative_atoms=list(res.blocking_negative_atoms),
        triggered_exception_atoms=list(res.triggered_exception_atoms),
        failed_constraints=failed_cons,
        supporting_atoms=list(res.supporting_atoms),
        source_ref=str(src) if src else None,
        user_message_hint=hint,
        clarification_priority=pri,
    )


def sort_clarification_keys_by_failed_paths(
    missing_keys: list[str],
    failed_path_records: list[FailedPathRecord],
) -> list[str]:
    """Reorder missing keys using lowest clarification_priority among records that mention the key."""
    if not failed_path_records:
        return list(missing_keys)
    pri_by_key: dict[str, int] = {}
    for rec in failed_path_records:
        p = rec.clarification_priority
        for k in missing_keys:
            if k in rec.failure_detail or any(k in str(x) for x in rec.missing_constraint_inputs):
                pri_by_key[k] = min(pri_by_key.get(k, 99), p)
        for m in rec.missing_constraint_inputs:
            if m in missing_keys:
                pri_by_key[m] = min(pri_by_key.get(m, 99), p)
    def sort_key(k: str) -> tuple[int, str]:
        return (pri_by_key.get(k, 50), k)
    return sorted(missing_keys, key=sort_key)
