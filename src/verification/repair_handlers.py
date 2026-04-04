"""Concrete repair steps invoked by repair_loop (re-parse / re-layer2 / re-answer)."""

from __future__ import annotations

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


def default_answer_regenerate(conclusion: str, attempt: int, hint: str, payload: dict[str, Any]) -> str:
    """Template regeneration — stable, uses repair context in output for traceability."""
    from generation.answer_generator import safe_regenerate_answer

    _ = hint, payload
    if attempt <= 1:
        return safe_regenerate_answer(conclusion)
    return f"{safe_regenerate_answer(conclusion)} (repair_attempt={attempt})"
