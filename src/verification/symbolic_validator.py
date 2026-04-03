"""Symbolic checks — slot consistency, goal vs rule head, answer vs goal."""

from __future__ import annotations

from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord


def check_parse_consistency(layer1: Layer1Parse, layer2: Layer2Parse) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if layer1.question_focus != "unknown" and layer2.goal.get("predicate") == "unknown":
        issues.append("layer2_goal_unknown_while_layer1_has_focus")
    if layer1.subject_text and layer2.subject_normalized:
        if len(layer1.subject_text) < 2 and len(layer2.subject_normalized) < 2:
            issues.append("subject_too_vague")
    return (len(issues) == 0), issues


def goal_matches_rule_head(goal: dict[str, Any], rule: RuleRecord) -> tuple[bool, list[str]]:
    gp = goal.get("predicate")
    ga = goal.get("args") or []
    hp = rule.head.predicate
    ha = rule.head.args
    if gp != hp:
        return False, [f"predicate_mismatch:{gp}!={hp}"]
    if len(ga) != len(ha):
        return False, [f"arity_mismatch:{len(ga)}!={len(ha)}"]
    return True, []


def check_answer_vs_goal(
    *,
    modality_expected: str,
    action_token_in_answer: str | None,
    goal_action: str | None,
) -> tuple[bool, list[str]]:
    ok = True
    diag: list[str] = []
    if goal_action and action_token_in_answer and goal_action not in action_token_in_answer and action_token_in_answer not in goal_action:
        ok = False
        diag.append("action_mismatch")
    if modality_expected in ("phải", "bat_buoc") and "không" in (action_token_in_answer or ""):
        ok = False
        diag.append("modality_possible_mismatch")
    return ok, diag


class SymbolicValidator:
    """Legacy skeleton for older pipeline stubs (schema/typing validation)."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def validate(self, payload: dict[str, Any]) -> Any:
        raise NotImplementedError
