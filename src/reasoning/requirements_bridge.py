"""Bridge `ReasoningRule` -> `RequirementItem` list (session keys + kind + atom payload)."""

from __future__ import annotations

from typing import Any

from reasoning.internal.codec import serialize_atom
from reasoning.internal.constraint_codec import serialize_constraint_session_key
from reasoning.internal.models import Atom, ReasoningRule
from schemas.reasoning import RequirementItem


def _item_from_atom(atom: Atom, kind: str, idx: int) -> RequirementItem:
    key = serialize_atom(atom)
    return RequirementItem(
        key=key,
        description=f"{kind} [{idx}] {atom.predicate}",
        predicate=atom.predicate,
        args=list(atom.args),
        requirement_kind=kind,
        atom_payload=atom.model_dump(mode="json"),
    )


def reasoning_rule_to_requirement_items(rr: ReasoningRule) -> list[RequirementItem]:
    """
    Thứ tự: positive -> negative -> exception -> constraints.
    Mỗi mục có `key` ổn định cho `fact_satisfies_requirement` (chuỗi boundary).
    """
    items: list[RequirementItem] = []
    i = 0
    for atom in rr.positive_conditions:
        items.append(_item_from_atom(atom, "positive", i))
        i += 1
    for atom in rr.negative_conditions:
        items.append(_item_from_atom(atom, "negative", i))
        i += 1
    for atom in rr.exception_conditions:
        items.append(_item_from_atom(atom, "exception", i))
        i += 1
    for j, c in enumerate(rr.constraints):
        key = serialize_constraint_session_key(c)
        items.append(
            RequirementItem(
                key=key,
                description=f"constraint [{j}] {type(c).__name__}",
                predicate=f"constraint:{type(c).__name__}",
                args=[],
                requirement_kind="constraint",
                atom_payload=_constraint_dump(c),
            )
        )
    return items


def _constraint_dump(c: Any) -> dict[str, Any]:
    if hasattr(c, "model_dump"):
        return c.model_dump(mode="json")
    return {"repr": repr(c)}
