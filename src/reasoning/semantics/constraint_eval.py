"""Evaluate structured constraints against boundary `known_facts` — structured status, not a single bool."""

from __future__ import annotations

from typing import Any

from reasoning.internal.constraint_codec import serialize_constraint_session_key
from reasoning.internal.models import (
    DeadlineConstraint,
    DossierConstraint,
    ThresholdConstraint,
    ThresholdNoteConstraint,
)
from reasoning.semantics.numeric_lookup import apply_unit_sanity, resolve_numeric_value_for_threshold
from reasoning.semantics.plan_models import ConstraintEvaluationResult, ConstraintEvalStatus


def evaluate_threshold_constraint(
    c: ThresholdConstraint, known_facts: dict[str, Any]
) -> ConstraintEvaluationResult:
    sk = serialize_constraint_session_key(c)
    op = (c.operator or "").strip()
    target = c.value

    raw = resolve_numeric_value_for_threshold(c, known_facts)
    lookup = apply_unit_sanity(raw, c)
    nl = lookup.model_dump(mode="json")

    if sk in known_facts and known_facts[sk] is False:
        return ConstraintEvaluationResult(
            constraint_type="ThresholdConstraint",
            status="failed",
            detail="explicit_false",
            session_key=sk,
            numeric_lookup=nl,
        )

    if lookup.unit_mismatch and lookup.limitation_note:
        return ConstraintEvaluationResult(
            constraint_type="ThresholdConstraint",
            status="unknown",
            detail=lookup.limitation_note,
            session_key=sk,
            numeric_lookup=nl,
        )

    if not lookup.found or lookup.value is None:
        if sk in known_facts and known_facts[sk] is True:
            return ConstraintEvaluationResult(
                constraint_type="ThresholdConstraint",
                status="unknown",
                detail="truthy_without_numeric",
                session_key=sk,
                numeric_lookup=nl,
            )
        return ConstraintEvaluationResult(
            constraint_type="ThresholdConstraint",
            status="missing_input",
            detail="missing_numeric_for_metric",
            session_key=sk,
            numeric_lookup=nl,
        )

    m = float(lookup.value)
    if target is None:
        return ConstraintEvaluationResult(
            constraint_type="ThresholdConstraint",
            status="unknown",
            detail="no_target_in_rule",
            session_key=sk,
            numeric_lookup=nl,
        )

    ok = False
    if op in (">=", "gte", "≥"):
        ok = m >= float(target)
    elif op in ("<=", "lte", "≤"):
        ok = m <= float(target)
    elif op in (">", "gt"):
        ok = m > float(target)
    elif op in ("<", "lt"):
        ok = m < float(target)
    elif op in ("==", "=", "eq"):
        ok = abs(m - float(target)) < 1e-9
    else:
        return ConstraintEvaluationResult(
            constraint_type="ThresholdConstraint",
            status="unknown",
            detail=f"unsupported_op:{op}",
            session_key=sk,
            numeric_lookup=nl,
        )

    st: ConstraintEvalStatus = "satisfied" if ok else "failed"
    return ConstraintEvaluationResult(
        constraint_type="ThresholdConstraint",
        status=st,
        detail=f"m={m} op={op} target={target}",
        session_key=sk,
        numeric_lookup=nl,
    )


def evaluate_deadline_constraint(
    c: DeadlineConstraint, known_facts: dict[str, Any]
) -> ConstraintEvaluationResult:
    sk = serialize_constraint_session_key(c)
    if sk in known_facts:
        v = known_facts[sk]
        if v is False:
            return ConstraintEvaluationResult(constraint_type="DeadlineConstraint", status="failed", session_key=sk)
        return ConstraintEvaluationResult(constraint_type="DeadlineConstraint", status="satisfied", session_key=sk)
    for k, v in known_facts.items():
        if isinstance(k, str) and ("deadline" in k or "moc_thoi_gian" in k or "ngay" in k):
            if v not in (False, None):
                return ConstraintEvaluationResult(constraint_type="DeadlineConstraint", status="satisfied", detail=k, session_key=sk)
    return ConstraintEvaluationResult(
        constraint_type="DeadlineConstraint", status="missing_input", detail="need_date_or_milestone", session_key=sk
    )


def evaluate_dossier_constraint(
    c: DossierConstraint, known_facts: dict[str, Any]
) -> ConstraintEvaluationResult:
    sk = serialize_constraint_session_key(c)
    if sk in known_facts:
        v = known_facts[sk]
        if v is False:
            return ConstraintEvaluationResult(constraint_type="DossierConstraint", status="failed", session_key=sk)
        return ConstraintEvaluationResult(constraint_type="DossierConstraint", status="satisfied", session_key=sk)
    for k, v in known_facts.items():
        if isinstance(k, str) and "dossier" in k and v not in (False, None):
            return ConstraintEvaluationResult(constraint_type="DossierConstraint", status="satisfied", detail=k, session_key=sk)
    return ConstraintEvaluationResult(
        constraint_type="DossierConstraint", status="missing_input", detail="need_dossier_status", session_key=sk
    )


def evaluate_threshold_note_constraint(
    c: ThresholdNoteConstraint, known_facts: dict[str, Any]
) -> ConstraintEvaluationResult:
    sk = serialize_constraint_session_key(c)
    if sk in known_facts:
        v = known_facts[sk]
        if v is False:
            return ConstraintEvaluationResult(constraint_type="ThresholdNoteConstraint", status="failed", session_key=sk)
        return ConstraintEvaluationResult(constraint_type="ThresholdNoteConstraint", status="satisfied", session_key=sk)
    return ConstraintEvaluationResult(
        constraint_type="ThresholdNoteConstraint", status="missing_input", detail="need_threshold_note_ack", session_key=sk
    )


def evaluate_constraint(c: Any, known_facts: dict[str, Any]) -> ConstraintEvaluationResult:
    if isinstance(c, ThresholdConstraint):
        return evaluate_threshold_constraint(c, known_facts)
    if isinstance(c, DeadlineConstraint):
        return evaluate_deadline_constraint(c, known_facts)
    if isinstance(c, DossierConstraint):
        return evaluate_dossier_constraint(c, known_facts)
    if isinstance(c, ThresholdNoteConstraint):
        return evaluate_threshold_note_constraint(c, known_facts)
    sk = f"constraint:other:{type(c).__name__}"
    return ConstraintEvaluationResult(constraint_type=type(c).__name__, status="unknown", detail="no_evaluator", session_key=sk)
