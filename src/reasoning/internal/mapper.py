"""Map `RuleRecord` (raw rulebase) -> `ReasoningRule` (internal reasoner schema)."""

from __future__ import annotations

from typing import Any

from schemas.rule import RuleRecord
from reasoning.internal.codec import atom_from_dict
from reasoning.internal.models import (
    Atom,
    AuxiliaryRecord,
    DeadlineConstraint,
    DossierConstraint,
    ReasoningRule,
    ThresholdConstraint,
    ThresholdNoteConstraint,
)


def _atom_from_clause(clause: dict[str, Any]) -> Atom | None:
    p = clause.get("predicate")
    if not p:
        return None
    return atom_from_dict(str(p), list(clause.get("args") or []))


def _head_threshold_constraint(head_args: list[Any]) -> ThresholdConstraint | None:
    if len(head_args) >= 4:
        return ThresholdConstraint(
            metric=str(head_args[0]) if head_args[0] is not None else None,
            operator=str(head_args[1]) if len(head_args) > 1 else None,
            value=_maybe_num(head_args[2]) if len(head_args) > 2 else None,
            unit=str(head_args[3]) if len(head_args) > 3 else None,
            raw_args=tuple(head_args),
        )
    if head_args:
        return ThresholdConstraint(raw_args=tuple(head_args))
    return None


def _maybe_num(x: Any) -> float | int | None:
    if isinstance(x, (int, float)):
        return x
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _clause_into_buckets(
    clause: dict[str, Any],
    positive: list[Atom],
    negative: list[Atom],
    exception: list[Atom],
    constraints: list[Any],
) -> None:
    atom = _atom_from_clause(clause)
    if atom is None:
        return
    pred = atom.predicate

    if pred in ("applies_if", "applies_to"):
        positive.append(atom)
        return
    if pred == "unless":
        negative.append(atom)
        return
    if pred == "exception_applies":
        exception.append(atom)
        return
    if pred == "threshold_note":
        constraints.append(ThresholdNoteConstraint(raw_args=atom.args))
        return
    if pred == "deadline":
        constraints.append(DeadlineConstraint(raw_args=atom.args))
        return
    if pred == "dossier":
        da = list(atom.args)
        proc = str(da[0]) if da else None
        docs: tuple[Any, ...] = tuple(da[1]) if len(da) > 1 and isinstance(da[1], (list, tuple)) else tuple(da[1:])
        constraints.append(DossierConstraint(procedure=proc, documents=docs, raw_args=atom.args))
        return
    # Unknown body predicate: treat as positive atom (backward compat with odd exports)
    positive.append(atom)


def _map_auxiliary(aux: list[dict[str, Any]]) -> tuple[list[AuxiliaryRecord], list[Any]]:
    out_aux: list[AuxiliaryRecord] = []
    extra_constraints: list[Any] = []
    for block in aux or []:
        if not isinstance(block, dict):
            continue
        kind = block.get("kind")
        head_d = block.get("head") or {}
        ha = _atom_from_clause(head_d) if head_d.get("predicate") else None
        body_atoms: list[Atom] = []
        for c in block.get("body") or []:
            if isinstance(c, dict) and c.get("predicate"):
                a = _atom_from_clause(c)
                if a:
                    body_atoms.append(a)
        out_aux.append(AuxiliaryRecord(kind=str(kind) if kind else None, head=ha, body_atoms=tuple(body_atoms)))
        if ha and ha.predicate == "dossier":
            da = list(ha.args)
            proc = str(da[0]) if da else None
            docs = tuple(da[1]) if len(da) > 1 and isinstance(da[1], (list, tuple)) else tuple(da[1:])
            extra_constraints.append(DossierConstraint(procedure=proc, documents=docs, raw_args=ha.args))
        for a in body_atoms:
            if a.predicate == "deadline":
                extra_constraints.append(DeadlineConstraint(raw_args=a.args))
    return out_aux, extra_constraints


def _constraints_from_head(rule: RuleRecord) -> list[Any]:
    lf = rule.logic_form or ""
    ha = list(rule.head.args or [])
    out: list[Any] = []
    if lf == "threshold" and ha:
        tc = _head_threshold_constraint(ha)
        if tc:
            out.append(tc)
    elif lf == "deadline" and ha:
        out.append(DeadlineConstraint(raw_args=tuple(ha)))
    elif lf == "dossier" and ha:
        proc = str(ha[0]) if ha else None
        docs = tuple(ha[1]) if len(ha) > 1 and isinstance(ha[1], (list, tuple)) else tuple(ha[1:])
        out.append(DossierConstraint(procedure=proc, documents=docs, raw_args=tuple(ha)))
    return out


def map_rule_record_to_reasoning_rule(rule: RuleRecord) -> ReasoningRule:
    """
    Không đọc/ghi file JSON — chỉ chiếu từ `RuleRecord` đã load.
    Head -> `goal_atom`; body -> positive / negative / exception / constraints; auxiliary giữ có kiểm soát.
    """
    goal_atom = (rule.head.predicate, *list(rule.head.args or []))

    positive: list[Atom] = []
    negative: list[Atom] = []
    exception: list[Atom] = []
    constraints: list[Any] = []

    constraints.extend(_constraints_from_head(rule))

    for clause in rule.body or []:
        if isinstance(clause, dict):
            _clause_into_buckets(clause, positive, negative, exception, constraints)

    aux_records, aux_cons = _map_auxiliary(list(rule.auxiliary_clauses or []))
    constraints.extend(aux_cons)

    prov = rule.metadata.get("provenance") or {}
    sr = prov.get("source_ref")
    srf = prov.get("source_ref_full")

    return ReasoningRule(
        rule_id=rule.rule_id,
        logic_form=rule.logic_form,
        goal_atom=goal_atom,
        positive_conditions=tuple(positive),
        negative_conditions=tuple(negative),
        exception_conditions=tuple(exception),
        constraints=tuple(constraints),
        auxiliary_outputs=tuple(aux_records),
        source_ref=str(sr) if sr else None,
        source_ref_full=str(srf) if srf else None,
        metadata=dict(rule.metadata),
    )
