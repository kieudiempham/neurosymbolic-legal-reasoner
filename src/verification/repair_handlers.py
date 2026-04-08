"""Concrete repair steps invoked by repair_loop (re-parse / re-layer2 / re-answer)."""

from __future__ import annotations

import os
import re
from typing import Any

from question_side.question_normalizer import build_layer2
from schemas.question_parse import Layer1Parse, Layer2Parse

# Align with symbolic_modes focus → predicate (minimal repair)
_FOCUS_TO_PRED: dict[str, str] = {
    "obligation": "obligation",
    "permission": "permission",
    "prohibition": "prohibition",
    "deadline": "deadline",
    "threshold": "threshold",
    "exception": "exception",
    "applicability": "applies_if",
    "dossier": "dossier",
    "legal_effect": "obligation",
    "authority": "obligation",
    "procedure": "obligation",
    "legal_consequence": "obligation",
    "unknown": "unknown",
}


def repair_layer2_from_payload(
    layer1: Layer1Parse,
    user_facts: list[str],
    payload: dict[str, Any],
) -> Layer2Parse:
    """Re-run layer2 builder, then apply goal alignment from repair diagnostics if needed."""
    base = build_layer2(layer1, list(user_facts))
    codes = set(payload.get("diagnostic_errors") or [])
    g = dict(base.goal or {})
    focus = layer1.question_focus
    want = _FOCUS_TO_PRED.get(focus, "unknown")

    if codes & {"goal_construction_error", "layer1_layer2_misalignment", "parse_slot_error"}:
        if want != "unknown" and str(g.get("predicate") or "") in ("unknown", ""):
            g["predicate"] = want if want != "unknown" else "obligation"
            if not g.get("args"):
                g["args"] = ["company_x", "hanh_vi", "doi_tuong"]
        if want != "unknown" and str(g.get("predicate") or "") != want and focus not in ("applicability",):
            g["predicate"] = want
            if len(g.get("args") or []) < 1:
                g["args"] = ["company_x", "hanh_vi", "doi_tuong"]

    qrc = f"{g.get('predicate', 'unknown')}:{','.join(str(a) for a in g.get('args', []))}"
    return base.model_copy(update={"goal": g, "query_rule_candidate": qrc})


def repair_parse_bundle(
    question_text: str,
    layer1: Layer1Parse,
    layer2: Layer2Parse,
    user_facts: list[str],
    payload: dict[str, Any],
    *,
    repair_hint: str = "",
) -> tuple[Layer1Parse, Layer2Parse, dict[str, Any]]:
    """
    Slot-aware repair: try LLM slot fix when API key exists and codes warrant Layer-1 touch;
    otherwise goal-only Layer-2 repair.
    """
    codes = list(payload.get("diagnostic_errors") or [])
    code_set = set(codes)
    has_key = bool((os.environ.get("LEGAL_QA_LLM_API_KEY") or os.environ.get("LLM_API_KEY") or "").strip())
    llm_touch = code_set & {"parse_slot_error", "layer1_layer2_misalignment", "fact_extraction_error"}

    if has_key and llm_touch:
        try:
            from question_side.llm_layer1_parser import repair_layer1_slots_llm

            l1_new, meta = repair_layer1_slots_llm(
                question_text,
                layer1,
                hint=repair_hint or "",
                diagnostic_codes=codes,
            )
            l2_new = build_layer2(l1_new, list(user_facts))
            trace = {
                "repair_kind": "llm_layer1_slots",
                "fields_touched": ["layer1"],
                "repair_backend": "llm",
                **{k: v for k, v in meta.items() if k in ("parser_model", "raw_llm_output")},
            }
            return l1_new, l2_new, trace
        except Exception:
            pass

    qt = (question_text or "").strip()
    lower_q = qt.lower()
    if "có quyền" in lower_q and (layer1.question_focus == "unknown" or layer1.subject_text == qt):
        subj = layer1.subject_text
        if lower_q.startswith("lao động"):
            subj = "lao động"
        action = layer1.action_text
        match = re.search(r"có quyền gì(?:\s+khi\s+(.+))?", lower_q)
        if match:
            action = (match.group(1) or "thực hiện quyền theo hợp đồng").strip(" ?.")
        l1_fixed = layer1.model_copy(
            update={
                "subject_text": subj,
                "action_text": action,
                "question_focus": "permission",
                "assertion_status": "ambiguous",
                "raw_notes": list(layer1.raw_notes or []) + ["heuristic_permission_repair"],
            }
        )
        l2_fixed = build_layer2(l1_fixed, list(user_facts))
        return l1_fixed, l2_fixed, {
            "repair_kind": "heuristic_layer1_permission",
            "fields_touched": ["layer1.subject_text", "layer1.action_text", "layer1.question_focus", "layer2.goal"],
            "repair_backend": "heuristic",
        }

    if code_set & {"goal_construction_error"} and not llm_touch:
        l2 = repair_layer2_from_payload(layer1, user_facts, payload)
        return layer1, l2, {"repair_kind": "layer2_goal", "fields_touched": ["layer2.goal"], "repair_backend": "heuristic"}

    l2 = repair_layer2_from_payload(layer1, user_facts, payload)
    return layer1, l2, {"repair_kind": "layer2_fallback", "fields_touched": ["layer2.goal"], "repair_backend": "heuristic"}


def default_answer_regenerate(conclusion: str, attempt: int, hint: str, payload: dict[str, Any]) -> str:
    """Template regeneration — stable, uses repair context in output for traceability."""
    from generation.answer_generator import safe_regenerate_answer

    _ = hint, payload
    if attempt <= 1:
        return safe_regenerate_answer(conclusion)
    return f"{safe_regenerate_answer(conclusion)} (repair_attempt={attempt})"
