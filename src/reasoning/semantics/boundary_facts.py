"""Map session `known_facts` (boundary dict) to atom-level truth checks — internal reasoning uses `Atom`."""

from __future__ import annotations

from typing import Any, Literal

from reasoning.internal.codec import canonicalize_atom, deserialize_atom, serialize_atom
from reasoning.internal.models import Atom

TruthStatus = Literal["true", "false", "missing"]


def canonicalize_atom_for_compare(atom: Atom) -> Atom:
    return canonicalize_atom(atom)


def atom_truth_status(atom: Atom, known_facts: dict[str, Any]) -> TruthStatus:
    """Whether an atom is asserted true, false, or unknown in boundary facts."""
    c = canonicalize_atom(atom)
    key = serialize_atom(c)
    if key in known_facts:
        v = known_facts[key]
        if v is False:
            return "false"
        if v is None:
            return "missing"
        return "true"
    for kk, v in known_facts.items():
        if v is False:
            continue
        try:
            other = deserialize_atom(kk)
        except Exception:
            continue
        oc = canonicalize_atom(other)
        if oc.predicate == c.predicate and oc.args == c.args:
            if v is False:
                return "false"
            return "true"
        if key in kk or kk in key:
            return "true"
    return "missing"


def known_atoms_from_facts(known_facts: dict[str, Any]) -> list[tuple[Atom, Any]]:
    """Deserialize boundary keys into `(Atom, value)` where parseable."""
    out: list[tuple[Atom, Any]] = []
    for k, v in known_facts.items():
        if not isinstance(k, str):
            continue
        if k.startswith("constraint:"):
            continue
        try:
            a = deserialize_atom(k)
        except Exception:
            continue
        out.append((canonicalize_atom(a), v))
    return out
