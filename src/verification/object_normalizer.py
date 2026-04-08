"""Normalize runtime objects before symbolic + NLI (boundary-safe dicts)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def _dump(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, BaseModel):
        return x.model_dump(mode="json")
    if isinstance(x, dict):
        return {str(k): _dump(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_dump(i) for i in x]
    return x


def normalize_parse_bundle(
    *,
    question_text: str,
    layer1: Any,
    layer2: Any,
) -> dict[str, Any]:
    return {
        "question_text": (question_text or "").strip(),
        "layer1": _dump(layer1),
        "layer2": _dump(layer2),
    }


def normalize_rule_bundle(
    *,
    layer2_goal: dict[str, Any],
    rule_candidate: Any,
    law_span: str | None,
    legal_frame: str | None,
) -> dict[str, Any]:
    return {
        "layer2_goal": dict(layer2_goal),
        "rule_candidate": _dump(rule_candidate),
        "law_span": (law_span or "").strip() or None,
        "legal_frame": (legal_frame or "").strip() or None,
    }


def normalize_backward_bundle(
    *,
    goal: dict[str, Any],
    selected_rule_id: str | None,
    backward_plan: dict[str, Any] | None,
    missing_facts: list[str] | None,
    requirements_ok: bool,
    requirement_artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "goal": dict(goal),
        "selected_rule_id": selected_rule_id,
        "backward_plan": dict(backward_plan or {}),
        "missing_facts": list(missing_facts or []),
        "requirements_ok": requirements_ok,
        "requirement_artifact": dict(requirement_artifact or {}),
    }


def normalize_forward_bundle(
    *,
    goal: dict[str, Any],
    conclusion: str,
    goal_achieved: bool,
    known_facts: dict[str, Any] | None,
    forward_result: dict[str, Any] | None,
    proof: dict[str, Any] | None,
    requirement_artifact: dict[str, Any] | None = None,
    selected_rule_id: str | None = None,
) -> dict[str, Any]:
    return {
        "goal": dict(goal),
        "conclusion": (conclusion or "").strip(),
        "goal_achieved": goal_achieved,
        "known_facts": dict(known_facts or {}),
        "forward_result": dict(forward_result or {}),
        "proof": dict(proof or {}),
        "requirement_artifact": dict(requirement_artifact or {}),
        "selected_rule_id": selected_rule_id,
    }


def normalize_answer_bundle(
    *,
    answer_text: str,
    conclusion: str,
    proof: dict[str, Any] | None,
    symbolic_ok: bool,
) -> dict[str, Any]:
    return {
        "answer_text": (answer_text or "").strip(),
        "conclusion": (conclusion or "").strip(),
        "proof": dict(proof or {}),
        "symbolic_ok": symbolic_ok,
    }
