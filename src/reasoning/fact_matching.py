"""Schema-aware fact matching for atoms vs working memory (Chặng A)."""

from __future__ import annotations

from typing import Any

from reasoning.internal.codec import canonicalize_atom, deserialize_atom, serialize_atom
from reasoning.internal.models import Atom
from reasoning.semantics.boundary_facts import atom_truth_status as _legacy_atom_truth_status
from schemas.structured_fact import StructuredFact
from runtime.domain_reasoning_policy import DomainReasoningPolicy, policy_from_context


def atoms_equal(a: Atom, b: Atom) -> bool:
    ca, cb = canonicalize_atom(a), canonicalize_atom(b)
    return ca.predicate == cb.predicate and tuple(ca.args) == tuple(cb.args)


def _structured_fact_to_atom(sf: StructuredFact) -> Atom:
    return canonicalize_atom(Atom(predicate=sf.predicate, args=tuple(sf.args)))


def atom_truth_status_ctx(
    atom: Atom,
    known_facts: dict[str, Any],
    *,
    structured_facts: dict[str, dict[str, Any]] | None,
    reasoning_context: Any | None = None,
    legacy_fuzzy: bool = True,
) -> str:
    """
    Return ``true`` / ``false`` / ``missing`` with predicate+args first, then policy on structured facts.
    """
    c = canonicalize_atom(atom)
    key = serialize_atom(c)

    if key in known_facts:
        v = known_facts[key]
        if v is False:
            return "false"
        if v is None:
            return "missing"
        return "true"

    if structured_facts:
        policy: DomainReasoningPolicy | None = (
            policy_from_context(reasoning_context) if reasoning_context is not None else None
        )
        for _k, blob in structured_facts.items():
            try:
                sf = StructuredFact.model_validate(blob)
            except Exception:
                continue
            if policy is not None and reasoning_context is not None:
                ok, _ = policy.allows_fact(sf, reasoning_context)
                if not ok:
                    continue
            sa = _structured_fact_to_atom(sf)
            if atoms_equal(sa, c):
                return "true"

    if legacy_fuzzy:
        return _legacy_atom_truth_status(atom, known_facts)
    return "missing"


def fact_satisfies_requirement_ctx(
    req_key: str,
    known_facts: dict[str, Any],
    *,
    structured_facts: dict[str, dict[str, Any]] | None = None,
    reasoning_context: Any | None = None,
) -> bool:
    """Structured check: parse req_key as atom if possible; else limited legacy fallback."""
    try:
        atom = deserialize_atom(req_key)
    except Exception:
        atom = None
    if atom is not None:
        return atom_truth_status_ctx(
            canonicalize_atom(atom),
            known_facts,
            structured_facts=structured_facts,
            reasoning_context=reasoning_context,
            legacy_fuzzy=True,
        ) == "true"

    for k, v in known_facts.items():
        if v is False:
            continue
        if v is None or v is True:
            if k == req_key:
                return True
    return False


def parse_legacy_fact_key_to_structured(fact_key: str, *, fact_origin: str, fact_domain: str) -> StructuredFact | None:
    """Best-effort parse ``predicate(args)`` string into StructuredFact."""
    try:
        a = deserialize_atom(fact_key)
        c = canonicalize_atom(a)
        sk = serialize_atom(c)
        return StructuredFact(
            fact_id=sk,
            predicate=c.predicate,
            args=list(c.args),
            fact_origin=fact_origin,  # type: ignore[arg-type]
            fact_domain=fact_domain,
            serialized_key=sk,
            provenance={"source": "legacy_key_parse"},
        )
    except Exception:
        return None
