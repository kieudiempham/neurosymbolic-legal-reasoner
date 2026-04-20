"""Map diagnostic error codes → repair module + hint (v5)."""

from __future__ import annotations

from typing import Any

# Taxonomy groups (strings stable for logging / tests)
PARSE_CODES = frozenset(
    {
        "parse_slot_error",
        "goal_construction_error",
        "fact_extraction_error",
        "layer1_layer2_misalignment",
    }
)
RULE_CODES = frozenset(
    {
        "rule_extraction_error",
        "rule_schema_error",
        "rule_modality_error",
        "rule_exception_error",
        "rule_deadline_error",
        "rule_threshold_error",
    }
)
BACKWARD_CODES = frozenset(
    {
        "backward_rule_selection_error",
        "backward_unification_error",
        "backward_semantic_family_mismatch",
        "backward_weak_grounding",
        "requirement_construction_error",
        "missing_fact_error",
    }
)
FORWARD_CODES = frozenset(
    {
        "forward_proof_error",
        "forward_constraint_error",
        "forward_exception_error",
        "forward_conclusion_error",
    }
)
ANSWER_CODES = frozenset(
    {
        "answer_semantic_drift",
        "answer_contradiction",
        "answer_overclaim",
        "answer_subject_action_mismatch",
        "answer_time_quantity_mismatch",
    }
)
RETRIEVAL_CODES = frozenset(
    {
        "retrieval_empty_error",
        "retrieval_low_recall_error",
        "retrieval_ranking_error",
    }
)


def repair_target_for_code(code: str) -> str:
    if code in PARSE_CODES:
        return "parser"
    if code in RULE_CODES:
        return "legal_frame_extractor_or_rule_builder"
    if code in {"backward_rule_selection_error", "backward_semantic_family_mismatch", "backward_weak_grounding"}:
        return "selected_rule_ranking"
    if code in {"backward_unification_error", "missing_fact_error", "requirement_construction_error"}:
        return "backward_requirement_extraction"
    if code in {"forward_constraint_error", "forward_exception_error", "forward_conclusion_error"}:
        return "forward_reasoner"
    if code == "forward_proof_error":
        return "forward_proof_construction"
    if code in ANSWER_CODES:
        return "answer_generation"
    if code in RETRIEVAL_CODES:
        return "retrieval"
    return "unspecified"


def repair_hint_for(code: str, *, mode: str) -> str:
    base = repair_target_for_code(code)
    return f"[{mode}] {code} → inspect module `{base}`."


def build_repair_payload(
    *,
    codes: list[str],
    mode: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ctx = dict(context or {})
    ctx["mode"] = mode
    ctx["diagnostic_errors"] = list(codes)
    ctx["repair_targets"] = [repair_target_for_code(c) for c in codes]
    return ctx
