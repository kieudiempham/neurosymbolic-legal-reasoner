"""
Structured numeric resolution for threshold constraints.

Convention (boundary keys — session-facing; reasoning uses `ThresholdConstraint` + this module):

1. **Explicit numeric slot (preferred)** — `numeric:{metric_slug}` → int | float
2. **Metric shorthand** — `metric:{metric_slug}` → int | float
3. **Constraint key with numeric value** — same key as `serialize_constraint_session_key(c)` when value is numeric
4. **Atom carriers** — deserialize keys to `Atom`; predicate == metric, or metric token in args, or predicates
   `numeric_metric` / `metric_value` / `gia_tri_dinh_luong` with (metric, value, unit?)
5. **Legacy heuristic** — substring match; flagged via `limitation_note`

Unit: shallow check only (`unit_mismatch` + note); no silent conversion.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from reasoning.internal.constraint_codec import serialize_constraint_session_key
from reasoning.internal.models import Atom, ThresholdConstraint
from reasoning.semantics.boundary_facts import known_atoms_from_facts

NumericSource = Literal[
    "explicit_numeric_key",
    "metric_session_key",
    "constraint_key_numeric",
    "atom_carrier",
    "legacy_heuristic",
    "none",
]


class NumericLookupResult(BaseModel):
    """Single place for threshold numeric resolution metadata."""

    model_config = {"extra": "forbid"}

    found: bool
    value: float | None = None
    unit: str | None = None
    source: NumericSource = "none"
    matched_key: str | None = None
    matched_atom: dict[str, Any] | None = None
    match_type: str = ""
    unit_mismatch: bool = False
    limitation_note: str = ""


NUMERIC_PREFIX = "numeric:"
METRIC_PREFIX = "metric:"


def _float_from(x: Any) -> float | None:
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _normalize_percent_vs_fraction(
    value: float,
    constraint_unit: str | None,
    rule_target: float | int | None,
) -> tuple[float, bool, str]:
    cu = (constraint_unit or "").lower()
    if cu in ("phan_tram", "%", "percent") and rule_target is not None:
        if 0 < value <= 1.0 and float(rule_target) > 1.0:
            return value, True, "value_looks_like_fraction_but_rule_target_is_percent_scale"
        if value > 1.0 and 0 < float(rule_target) <= 1.0:
            return value, True, "value_looks_like_percent_but_rule_target_is_fraction_scale"
    return value, False, ""


def _atom_match_metric(atom: Atom, metric: str) -> NumericLookupResult:
    dumped = atom.model_dump(mode="json")
    if atom.predicate == metric:
        for a in atom.args:
            fv = _float_from(a)
            if fv is not None:
                return NumericLookupResult(
                    found=True,
                    value=fv,
                    source="atom_carrier",
                    matched_atom=dumped,
                    match_type="predicate_equals_metric",
                )
    args_str = [str(x) for x in atom.args]
    if metric in args_str:
        for a in atom.args:
            fv = _float_from(a)
            if fv is not None:
                return NumericLookupResult(
                    found=True,
                    value=fv,
                    source="atom_carrier",
                    matched_atom=dumped,
                    match_type="metric_token_in_args",
                )
    if atom.predicate in ("numeric_metric", "metric_value", "gia_tri_dinh_luong"):
        if len(atom.args) >= 2 and str(atom.args[0]) == metric:
            fv = _float_from(atom.args[1])
            if fv is not None:
                u = str(atom.args[2]) if len(atom.args) > 2 else None
                return NumericLookupResult(
                    found=True,
                    value=fv,
                    unit=u,
                    source="atom_carrier",
                    matched_atom=dumped,
                    match_type="numeric_metric_predicate",
                )
    return NumericLookupResult(found=False, source="none")


def extract_numeric_from_atoms_for_metric(metric: str | None, known_facts: dict[str, Any]) -> NumericLookupResult:
    if not metric:
        return NumericLookupResult(found=False, source="none", match_type="no_metric")
    m = metric.strip()
    for atom, _val in known_atoms_from_facts(known_facts):
        r = _atom_match_metric(atom, m)
        if r.found:
            return r
    return NumericLookupResult(found=False, source="none", match_type="no_atom_match")


def _legacy_numeric_scan(metric: str | None, known_facts: dict[str, Any]) -> NumericLookupResult:
    if not metric:
        return NumericLookupResult(
            found=False,
            source="legacy_heuristic",
            match_type="legacy",
            limitation_note="no_metric_for_legacy_scan",
        )
    m = metric.lower().replace(" ", "_")
    for k, v in known_facts.items():
        if not isinstance(k, str):
            continue
        kl = k.lower()
        if m in kl and isinstance(v, (int, float)):
            return NumericLookupResult(
                found=True,
                value=float(v),
                source="legacy_heuristic",
                matched_key=k,
                match_type="substring_key_metric",
                limitation_note="legacy_substring_match_on_key",
            )
    for k, v in known_facts.items():
        if isinstance(v, (int, float)) and ("threshold" in str(k).lower() or "ty_le" in str(k).lower()):
            return NumericLookupResult(
                found=True,
                value=float(v),
                source="legacy_heuristic",
                matched_key=str(k),
                match_type="first_numeric_threshold_like_key",
                limitation_note="legacy_heuristic_weak_association",
            )
    return NumericLookupResult(found=False, source="legacy_heuristic", limitation_note="legacy_scan_empty")


def resolve_numeric_value_for_threshold(
    c: ThresholdConstraint,
    known_facts: dict[str, Any],
) -> NumericLookupResult:
    """
    Resolve numeric input for a threshold constraint using conventions above, then legacy fallback.
    """
    metric = (c.metric or "").strip() or None
    sk = serialize_constraint_session_key(c)

    if metric:
        nk = f"{NUMERIC_PREFIX}{metric}"
        if nk in known_facts:
            fv = _float_from(known_facts[nk])
            if fv is not None:
                return NumericLookupResult(
                    found=True,
                    value=fv,
                    source="explicit_numeric_key",
                    matched_key=nk,
                    match_type="numeric_prefix",
                )
        mk = f"{METRIC_PREFIX}{metric}"
        if mk in known_facts:
            fv = _float_from(known_facts[mk])
            if fv is not None:
                return NumericLookupResult(
                    found=True,
                    value=fv,
                    source="metric_session_key",
                    matched_key=mk,
                    match_type="metric_prefix",
                )

    if sk in known_facts:
        fv = _float_from(known_facts[sk])
        if fv is not None:
            return NumericLookupResult(
                found=True,
                value=fv,
                source="constraint_key_numeric",
                matched_key=sk,
                match_type="constraint_session_numeric_value",
            )

    atom_res = extract_numeric_from_atoms_for_metric(metric, known_facts)
    if atom_res.found:
        return atom_res

    leg = _legacy_numeric_scan(metric, known_facts)
    if leg.found:
        return leg

    return NumericLookupResult(found=False, source="none", match_type="not_found")


def apply_unit_sanity(
    lookup: NumericLookupResult,
    c: ThresholdConstraint,
) -> NumericLookupResult:
    """Attach unit_mismatch note without changing numeric compare policy here (caller decides unknown vs compare)."""
    if not lookup.found or lookup.value is None:
        return lookup
    v, mismatch, note = _normalize_percent_vs_fraction(
        lookup.value, c.unit, c.value if isinstance(c.value, (int, float)) else None
    )
    if not mismatch:
        return lookup
    return lookup.model_copy(update={"value": v, "unit_mismatch": True, "limitation_note": note or lookup.limitation_note})
