"""Turn logical sketches / goals into short Vietnamese text for NLI."""

from __future__ import annotations

from typing import Any


def verbalize_goal(goal: dict[str, Any]) -> str:
    pred = goal.get("predicate") or "unknown"
    args = goal.get("args") or []
    if pred == "obligation" and len(args) >= 3:
        subj, act, obj = args[0], args[1], args[2]
        return f"Chủ thể {subj} có nghĩa vụ thực hiện hành vi {act} đối với {obj}."
    if pred == "permission" and len(args) >= 3:
        return f"Chủ thể {args[0]} được phép thực hiện {args[1]} với đối tượng {args[2]}."
    if pred == "prohibition" and len(args) >= 3:
        return f"Chủ thể {args[0]} bị cấm thực hiện {args[1]} liên quan {args[2]}."
    if pred == "deadline" and len(args) >= 4:
        return f"Hạn {args[2]} {args[1]} kể từ neo thời gian {args[3]} cho hành động {args[0]}."
    if pred == "threshold" and len(args) >= 4:
        return f"Ngưỡng {args[0]} so sánh {args[1]} giá trị {args[2]} đơn vị {args[3]}."
    return f"Mục tiêu logic {pred}({', '.join(str(a) for a in args)})."


def verbalize_fact_atom(fact: str) -> str:
    if "(" in fact and fact.endswith(")"):
        name, rest = fact.split("(", 1)
        inner = rest[:-1]
        return f"Điều kiện {name} với {inner}."
    return f"Điều kiện {fact}."


def verbalize_layer1_subject(subject_text: str) -> str:
    return f"Người hỏi nói về {subject_text}."


def verbalize_answer_conclusion(answer_text: str, conclusion: str) -> str:
    return f"Kết luận hình thức: {conclusion}. Câu trả lời: {answer_text}"


def verbalize_question_text(question_text: str) -> str:
    return f"Câu hỏi gốc: {question_text.strip()}"


def verbalize_layer2_sketch(layer2_summary: str) -> str:
    return f"Bản phân tích Layer-2: {layer2_summary}"


def verbalize_rule_candidate(rule_id: str, logic_form: str, head_pred: str) -> str:
    return f"Luật ứng viên {rule_id} dạng {logic_form} với đầu {head_pred}."


def verbalize_law_span(law_span: str) -> str:
    return f"Đoạn căn cứ pháp lý: {law_span.strip()}"


def verbalize_backward_plan(goal: dict[str, Any], selected_rule_id: str | None) -> str:
    g = verbalize_goal(goal)
    return f"Mục tiêu suy luận: {g} Luật chọn: {selected_rule_id}."


def verbalize_forward_failure(forward_result: dict[str, Any]) -> str:
    fr = str(forward_result.get("failure_reason") or "")
    gr = forward_result.get("goal_reached")
    return f"Forward: goal_reached={gr}, failure_reason={fr}."


def verbalize_proof_brief(proof: dict[str, Any]) -> str:
    steps = proof.get("proof_steps") or []
    n = len(steps) if isinstance(steps, list) else 0
    dc = proof.get("derived_conclusion") or ""
    return f"Chứng minh có {n} bước; kết luận hình thức trong proof: {dc}."
