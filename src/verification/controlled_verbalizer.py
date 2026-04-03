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
