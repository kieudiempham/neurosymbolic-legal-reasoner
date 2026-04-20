"""Generate clarification questions for missing symbolic requirements (v5 typed + prioritized)."""

from __future__ import annotations

from typing import Any

from reasoning.clarification_types import (
    clarification_question_for_kind,
    expected_answer_type,
    infer_target_kind,
    materialize_clarification_target,
    priority_for_kind,
)
from reasoning.internal.codec import serialize_atom
from reasoning.internal.models import Atom
from reasoning.semantics.failed_path_hints import sort_clarification_keys_by_failed_paths
from reasoning.semantics.plan_models import FailedPathRecord
from schemas.reasoning import RequirementItem


def clarification_for_missing_fact(fact_key: str, requirement_kind: str | None = None) -> str:
    """Backward-compatible entry point — delegates to typed templates."""
    kind = infer_target_kind(fact_key, requirement_kind)
    return clarification_question_for_kind(kind, fact_key, requirement_kind=requirement_kind)


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


def build_parse_ambiguity_prompts(ambiguities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn parse-time ambiguities into clarification rows (fact_key parse_amb:*)."""
    out: list[dict[str, Any]] = []
    for i, a in enumerate(ambiguities):
        cands = a.get("candidates") or []
        if not cands:
            continue
        kind = str(a.get("type") or "ambiguous_condition")
        opts = [str(x) for x in cands[:8]]
        qtext = (
            f"Làm rõ điều kiện/chủ thể: chọn phương án gần đúng nhất với ý bạn "
            f"(gửi value đúng một trong các chuỗi atom sau): {', '.join(opts)}"
        )
        pri = int(a.get("priority", 50))
        out.append(
            {
                "fact_key": f"parse_amb:{kind}:{i}",
                "question_text": qtext,
                "reason_hint": str(a.get("blocking_reason") or a.get("type") or ""),
                "target_kind": kind,
                "expected_type": "choice",
                "priority": pri,
                "options": opts,
                "blocking_reason": str(a.get("blocking_reason") or ""),
            }
        )
    return out


def merge_clarification_prompts_unified(
    parse_prompts: list[dict[str, Any]],
    backward_prompts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Parse / ambiguity first (lower priority number), then backward missing facts."""
    merged: list[dict[str, Any]] = []
    for p in parse_prompts:
        if "priority" not in p:
            p["priority"] = 5
        merged.append(dict(p))
    for p in backward_prompts:
        row = dict(p)
        row.setdefault("priority", 50)
        merged.append(row)
    merged.sort(key=lambda x: int(x.get("priority", 99)))
    return merged


def build_clarification_prompts_from_requirements(
    missing_keys: list[str],
    requirement_set: list[RequirementItem],
    backward_plan: dict[str, Any] | None = None,
    forward_result: dict[str, Any] | None = None,
    *,
    related_rule_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Typed clarification: target_kind, expected_type, priority, optional related_rule_id trace.
    """
    keys = list(missing_keys)
    if forward_result:
        raw = forward_result.get("failed_path_records") or []
        recs = [FailedPathRecord.model_validate(x) for x in raw if x]
        keys = sort_clarification_keys_by_failed_paths(keys, recs)
    by_key = {r.key: r for r in requirement_set}
    plan_q = _questions_from_backward_plan(backward_plan) if backward_plan else {}
    hint = best_forward_failure_hint(forward_result)
    out: list[dict[str, Any]] = []
    seen_public_fact_keys: set[str] = set()
    for k in keys:
        ri = by_key.get(k)
        materialized = materialize_clarification_target(
            k,
            requirement_kind=ri.requirement_kind if ri else None,
            fallback_text=plan_q.get(k) or "",
        )
        public_key = str(materialized.get("fact_key") or k)
        source_key = str(materialized.get("source_fact_key") or k)
        if public_key in seen_public_fact_keys:
            continue
        seen_public_fact_keys.add(public_key)

        kind = str(materialized.get("target_kind") or infer_target_kind(k, ri.requirement_kind if ri else None))
        exp_type = str(materialized.get("expected_type") or expected_answer_type(kind))
        pri = priority_for_kind(kind)
        row: dict[str, Any] = {
            "fact_key": public_key,
            "source_fact_key": source_key,
            "target_kind": kind,
            "expected_type": exp_type,
            "priority": pri,
            "related_rule_id": related_rule_id or "",
        }
        options = list(materialized.get("options") or [])
        if options:
            row["options"] = [str(x) for x in options if str(x).strip()]

        # Do not leak internal placeholders in user-facing question text.
        if bool(materialized.get("is_placeholder")):
            row["question_text"] = str(materialized.get("question_text") or "")
        elif k in plan_q and plan_q[k]:
            row["question_text"] = plan_q[k]
        else:
            row["question_text"] = str(materialized.get("question_text") or "") or clarification_question_for_kind(
                kind, k, requirement_kind=ri.requirement_kind if ri else None
            )
        if hint:
            row["reason_hint"] = hint
        row["reason"] = row.get("reason_hint") or f"need_input:{kind}"
        row.setdefault("reason_hint", row["reason"])
        out.append(row)
    return out


def filter_clarification_targets(
    missing_keys: list[str],
    *,
    known_facts: dict[str, Any] | None = None,
    parse_layer2: Any | None = None,
) -> list[str]:
    """Do not ask clarification for facts already known or already present in parse output."""
    known = set(str(k) for k in (known_facts or {}).keys())
    parsed: set[str] = set()
    if parse_layer2 is not None:
        for seq_name in ("condition_atoms", "facts"):
            seq = getattr(parse_layer2, seq_name, None) or []
            for x in seq:
                sx = str(x).strip()
                if sx:
                    parsed.add(sx)
        goal = getattr(parse_layer2, "goal", None) or {}
        if isinstance(goal, dict):
            gp = str(goal.get("predicate") or "").strip()
            gargs = list(goal.get("args") or [])
            if gp:
                parsed.add(f"{gp}({', '.join(str(a) for a in gargs)})")

    out: list[str] = []
    for key in missing_keys:
        sk = str(key).strip()
        if not sk:
            continue
        if sk in known or sk in parsed:
            continue
        out.append(sk)
    return out
