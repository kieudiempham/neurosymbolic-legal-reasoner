"""Controlled verbalization for NLI — mode-specific templates, explicit slots, guardrails."""

from __future__ import annotations

import re
from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord


def verbalize_goal(goal: dict[str, Any]) -> str:
    pred = goal.get("predicate") or "unknown"
    args = goal.get("args") or []
    if pred == "obligation" and len(args) >= 3:
        subj, act, obj = args[0], args[1], args[2]
        return (
            f"Chủ thể [{subj}] có nghĩa vụ thực hiện hành vi [{act}] đối với [{obj}]. "
            f"Modality: bắt buộc."
        )
    if pred == "permission" and len(args) >= 3:
        return (
            f"Chủ thể [{args[0]}] được phép thực hiện [{args[1]}] với đối tượng [{args[2]}]. "
            f"Modality: được phép."
        )
    if pred == "prohibition" and len(args) >= 3:
        return (
            f"Chủ thể [{args[0]}] bị cấm thực hiện [{args[1]}] liên quan [{args[2]}]. "
            f"Modality: cấm."
        )
    if pred == "deadline" and len(args) >= 4:
        return (
            f"Hạn [{args[2]}] cho [{args[1]}] kể từ mốc [{args[3]}] cho hành động [{args[0]}]. "
            f"Thời hạn/deadline được nêu rõ."
        )
    if pred == "threshold" and len(args) >= 4:
        return (
            f"Ngưỡng: [{args[0]}] so sánh [{args[1]}] giá trị [{args[2]}] đơn vị [{args[3]}]. "
            f"Số lượng/ngưỡng được nêu rõ."
        )
    return f"Mục tiêu logic {pred}({', '.join(str(a) for a in args)})."


def verbalize_fact_atom(fact: str) -> str:
    if "(" in fact and fact.endswith(")"):
        name, rest = fact.split("(", 1)
        inner = rest[:-1]
        return f"Điều kiện {name} với {inner}."
    return f"Điều kiện {fact}."


def verbalize_layer1_subject(subject_text: str) -> str:
    return f"Subject (chủ thể câu hỏi): [{subject_text}]."


def verbalize_answer_conclusion(answer_text: str, conclusion: str) -> str:
    return f"Kết luận hình thức: [{conclusion}]. Câu trả lời người dùng: [{answer_text}]"


def verbalize_question_text(question_text: str) -> str:
    return f"Câu hỏi gốc (verbatim): {question_text.strip()}"


def verbalize_layer2_sketch(layer2_summary: str) -> str:
    return f"Bản phân tích Layer-2: {layer2_summary}"


def verbalize_rule_candidate(rule_id: str, logic_form: str, head_pred: str) -> str:
    return (
        f"Rule [{rule_id}]: logic_form=[{logic_form}], head_predicate=[{head_pred}]. "
        f"Mapping luật ứng viên cho khung suy luận."
    )


def verbalize_law_span(law_span: str) -> str:
    return f"Đoạn căn cứ pháp lý (law_span/source): {law_span.strip()}"


def verbalize_backward_plan(goal: dict[str, Any], selected_rule_id: str | None) -> str:
    g = verbalize_goal(goal)
    return f"Mục tiêu suy luận: {g} | Luật đã chọn: [{selected_rule_id}]."


def verbalize_forward_failure(forward_result: dict[str, Any]) -> str:
    fr = str(forward_result.get("failure_reason") or "")
    gr = forward_result.get("goal_reached")
    return f"Forward: goal_reached={gr}, failure_reason=[{fr}]."


def verbalize_proof_brief(proof: dict[str, Any]) -> str:
    steps = proof.get("proof_steps") or []
    n = len(steps) if isinstance(steps, list) else 0
    dc = proof.get("derived_conclusion") or ""
    parts = [f"Proof có {n} bước; kết luận trong proof: [{dc}]."]
    if isinstance(steps, list):
        for i, st in enumerate(steps[:5]):
            if isinstance(st, dict):
                parts.append(f"Bước {i + 1}: [{st.get('description', '')}]")
    return " ".join(parts)


def _facts_summary(layer2: Layer2Parse) -> str:
    facts = layer2.facts or []
    atoms = layer2.condition_atoms or []
    return f"Sự kiện người dùng ({len(facts)}): {', '.join(facts[:6])}. Điều kiện ({len(atoms)}): {', '.join(atoms[:4])}."


def verbalize_parse_mode(
    question_text: str,
    layer1: Layer1Parse,
    layer2: Layer2Parse,
) -> tuple[str, str, str]:
    """Premise = question + layer1 summary; hypothesis = layer2 goal + facts summary."""
    l1 = (
        f"Layer1: subject=[{layer1.subject_text}], action=[{layer1.action_text}], "
        f"modality=[{layer1.modality_text}], focus=[{layer1.question_focus}], "
        f"assertion_status=[{layer1.assertion_status}]."
    )
    premise = f"{verbalize_question_text(question_text)} | {l1}"
    hyp = f"{verbalize_goal(layer2.goal)} | {_facts_summary(layer2)}"
    return premise, hyp, "parse_v2_question_layer1_vs_goal_facts"


def verbalize_rule_mode(
    law_span: str | None,
    legal_frame: str | None,
    rule: RuleRecord | None,
) -> tuple[str, str, str]:
    lf = (legal_frame or "").strip() or "(không có legal_frame)"
    if not rule:
        return (
            verbalize_law_span(law_span or ""),
            "Không có rule ứng viên.",
            "rule_v2_no_rule",
        )
    body_preds = [str((c or {}).get("predicate")) for c in (rule.body or []) if isinstance(c, dict)]
    exc = "exception_applies" in body_preds
    premise = f"{verbalize_law_span(law_span or '')} | legal_frame=[{lf}] | body_predicates={body_preds} | có_exception_body={exc}"
    hyp = verbalize_rule_candidate(rule.rule_id, rule.logic_form, rule.head.predicate if rule.head else "")
    if rule.head and rule.head.args:
        hyp += f" | head_args={rule.head.args}"
    return premise, hyp, "rule_v2_law_vs_candidate"


def verbalize_backward_mode(
    goal: dict[str, Any],
    selected_rule_id: str | None,
    backward_plan: dict[str, Any] | None,
    missing_facts: list[str] | None,
) -> tuple[str, str, str]:
    bp = backward_plan or {}
    cands = bp.get("candidates") or []
    req_line = f"candidates_n={len(cands)} missing={[', '.join(missing_facts or [])]}"
    premise = f"{verbalize_backward_plan(goal, selected_rule_id)} | {req_line}"
    hyp = verbalize_goal(goal)
    return premise, hyp, "backward_v2_plan_vs_goal"


def verbalize_forward_mode(
    goal: dict[str, Any],
    known_facts: dict[str, Any] | None,
    proof: dict[str, Any] | None,
    forward_result: dict[str, Any] | None,
    conclusion: str,
) -> tuple[str, str, str]:
    kf = list((known_facts or {}).keys())[:12]
    ktxt = f"Sự kiện đã biết ({len(kf)}): {', '.join(kf)}."
    prem_parts = [verbalize_goal(goal), ktxt, verbalize_proof_brief(proof or {}), verbalize_forward_failure(forward_result or {})]
    premise = " ".join(prem_parts)
    hyp = f"Kết luận cần kiểm tra: [{conclusion}]"
    return premise, hyp, "forward_v2_facts_proof_vs_conclusion"


def verbalize_answer_mode(
    answer_text: str,
    conclusion: str,
    proof: dict[str, Any] | None,
) -> tuple[str, str, str]:
    ps = verbalize_proof_brief(proof or {})
    premise = f"Kết luận logic: [{conclusion}] | {ps}"
    hyp = f"Câu trả lời: [{answer_text}]"
    return premise, hyp, "answer_v2_conclusion_proof_vs_answer"


def verbalization_guardrails(
    *,
    mode: str,
    layer1: Layer1Parse | None = None,
    layer2: Layer2Parse | None = None,
    goal: dict[str, Any] | None = None,
    premise: str = "",
    hypothesis: str = "",
    conclusion: str = "",
) -> list[str]:
    """Lightweight warnings when key slots may be missing from verbalized strings."""
    w: list[str] = []
    g = goal or (layer2.goal if layer2 else None) or {}
    pred = str(g.get("predicate") or "")
    args = g.get("args") or []

    if mode == "parse_verification" and layer1:
        if not (layer1.subject_text or "").strip():
            w.append("guardrail:missing_subject_layer1")
        if not (layer1.modality_text or "").strip():
            w.append("guardrail:missing_modality_layer1")

    if pred == "threshold" and mode in ("parse_verification", "rule_verification", "backward_verification"):
        if len(args) < 4 and "ngưỡng" not in hypothesis.lower():
            w.append("guardrail:threshold_args_incomplete")

    if pred == "deadline" and layer2 and mode == "parse_verification":
        if len(args) < 3 and "hạn" not in hypothesis.lower():
            w.append("guardrail:deadline_underverbalized")

    if "exception_applies" in premise and "exception" not in hypothesis.lower():
        w.append("guardrail:exception_only_in_premise")

    if mode == "answer_verification" and conclusion.strip() and conclusion.strip() not in premise:
        w.append("guardrail:conclusion_not_in_premise")

    if re.search(r"\[\s*\]", premise + hypothesis):
        w.append("guardrail:empty_bracket_placeholder")

    return w
