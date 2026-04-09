"""Unification and substitution over `Atom` / `ReasoningRule` (internal source of truth)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from reasoning.internal.codec import canonicalize_atom
from reasoning.internal.models import (
    Atom,
    DeadlineConstraint,
    DossierConstraint,
    ReasoningRule,
    ThresholdConstraint,
    ThresholdNoteConstraint,
)
from utils.text import lower_fold


class Substitution(BaseModel):
    """Variable -> ground term bindings (string keys for `_x`-style variables)."""

    model_config = ConfigDict(frozen=True)

    mapping: dict[str, Any] = Field(default_factory=dict)

    @staticmethod
    def empty() -> "Substitution":
        return Substitution(mapping={})

    def get(self, k: str) -> Any | None:
        return self.mapping.get(k)

    def merged(self, other: "Substitution") -> "Substitution":
        m = dict(self.mapping)
        for kk, vv in other.mapping.items():
            m[kk] = vv
        return Substitution(mapping=m)


def is_variable(term: Any) -> bool:
    if not isinstance(term, str):
        return False
    t = term.strip()
    return t.endswith("_x") or t in ("company_x", "doanh_nghiep_x", "subject_x")


def _fuzzy_equal(a: Any, b: Any) -> bool:
    if a == b:
        return True
    gs, hs = str(a), str(b)
    if gs == hs:
        return True
    tg = set(lower_fold(gs.replace("_", " ")).split())
    th = set(lower_fold(hs.replace("_", " ")).split())
    if not tg or not th:
        return False
    return len(tg & th) / max(1, len(tg | th)) >= 0.34


def _normalize_predicate_token(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return ""
    folded = lower_fold(s)
    folded = folded.replace("-", "_").replace(" ", "_")
    while "__" in folded:
        folded = folded.replace("__", "_")
    return folded.strip("_")


def _is_empty_arg(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _trim_trailing_empty_args(args: list[Any]) -> list[Any]:
    out = list(args)
    while out and _is_empty_arg(out[-1]):
        out.pop()
    return out


def unify_terms(a: Any, b: Any, subst: Substitution) -> Substitution | None:
    """Unify two terms; extend `subst` or return None."""
    if is_variable(a):
        if a in subst.mapping:
            return unify_terms(subst.mapping[a], b, subst)
        return subst.merged(Substitution(mapping={a: b}))
    if is_variable(b):
        if b in subst.mapping:
            return unify_terms(a, subst.mapping[b], subst)
        return subst.merged(Substitution(mapping={b: a}))
    if _fuzzy_equal(a, b):
        return subst
    return None


def unify_atoms(left: Atom, right: Atom, subst: Substitution) -> Substitution | None:
    if left.predicate != right.predicate:
        return None
    la, ra = list(left.args), list(right.args)
    if len(la) != len(ra):
        return None
    s = subst
    for x, y in zip(la, ra):
        u = unify_terms(x, y, s)
        if u is None:
            return None
        s = u
    return s


def apply_substitution_to_term(term: Any, subst: Substitution) -> Any:
    if is_variable(term) and term in subst.mapping:
        return apply_substitution_to_term(subst.mapping[term], subst)
    if isinstance(term, tuple):
        return tuple(apply_substitution_to_term(x, subst) for x in term)
    if isinstance(term, list):
        return [apply_substitution_to_term(x, subst) for x in term]
    return term


def apply_substitution_to_atom(atom: Atom, subst: Substitution) -> Atom:
    pred = apply_substitution_to_term(atom.predicate, subst)
    args = tuple(apply_substitution_to_term(a, subst) for a in atom.args)
    return canonicalize_atom(Atom(predicate=str(pred), args=args))


def apply_substitution_to_goal_tuple(goal_atom: tuple[Any, ...], subst: Substitution) -> tuple[Any, ...]:
    return tuple(apply_substitution_to_term(x, subst) for x in goal_atom)


def apply_substitution_to_conditions(atoms: tuple[Atom, ...], subst: Substitution) -> tuple[Atom, ...]:
    return tuple(apply_substitution_to_atom(a, subst) for a in atoms)


def apply_substitution_to_constraint(c: Any, subst: Substitution) -> Any:
    if isinstance(c, ThresholdConstraint):
        return c.model_copy(
            update={
                "metric": apply_substitution_to_term(c.metric, subst) if c.metric is not None else None,
                "operator": apply_substitution_to_term(c.operator, subst) if c.operator is not None else None,
                "value": apply_substitution_to_term(c.value, subst) if c.value is not None else None,
                "unit": apply_substitution_to_term(c.unit, subst) if c.unit is not None else None,
                "raw_args": tuple(apply_substitution_to_term(x, subst) for x in c.raw_args),
            }
        )
    if isinstance(c, DeadlineConstraint):
        return c.model_copy(
            update={"raw_args": tuple(apply_substitution_to_term(x, subst) for x in c.raw_args)}
        )
    if isinstance(c, DossierConstraint):
        return c.model_copy(
            update={
                "procedure": apply_substitution_to_term(c.procedure, subst) if c.procedure else None,
                "documents": tuple(apply_substitution_to_term(x, subst) for x in c.documents),
                "raw_args": tuple(apply_substitution_to_term(x, subst) for x in c.raw_args),
            }
        )
    if isinstance(c, ThresholdNoteConstraint):
        return c.model_copy(
            update={"raw_args": tuple(apply_substitution_to_term(x, subst) for x in c.raw_args)}
        )
    return deepcopy(c)


def apply_substitution_to_reasoning_rule(rr: ReasoningRule, subst: Substitution) -> ReasoningRule:
    ga = apply_substitution_to_goal_tuple(rr.goal_atom, subst)
    pos = apply_substitution_to_conditions(rr.positive_conditions, subst)
    neg = apply_substitution_to_conditions(rr.negative_conditions, subst)
    exc = apply_substitution_to_conditions(rr.exception_conditions, subst)
    cons = tuple(apply_substitution_to_constraint(c, subst) for c in rr.constraints)
    return rr.model_copy(
        update={
            "goal_atom": ga,
            "positive_conditions": pos,
            "negative_conditions": neg,
            "exception_conditions": exc,
            "constraints": cons,
        }
    )


def unify_goal_dict_with_goal_atom(
    goal: dict[str, Any],
    goal_atom: tuple[Any, ...],
    subst: Substitution | None = None,
    *,
    reasoning_context: Any | None = None,
    rule: Any | None = None,
    domain_policy: Any | None = None,
) -> tuple[Substitution | None, str | None]:
    """
    Unify runtime goal dict with rule head `goal_atom`.
    Returns (substitution, failure_reason).

    When ``reasoning_context`` + ``rule`` are set, domain boundary is enforced before structural unify.
    """
    if (
        reasoning_context is not None
        and rule is not None
        and getattr(reasoning_context, "strict_domain_enforcement", False)
    ):
        from runtime.domain_reasoning_policy import DomainReasoningPolicy, policy_from_context

        pol: DomainReasoningPolicy = domain_policy if domain_policy is not None else policy_from_context(reasoning_context)
        ok, reason = pol.allows_unification(rule, reasoning_context)
        if not ok:
            return None, reason or "unification_rejected_by_domain"
    if not goal_atom:
        return None, "empty_goal_atom"
    gp = goal.get("predicate")
    ga = _trim_trailing_empty_args(list(goal.get("args") or []))
    ha = _trim_trailing_empty_args(list(goal_atom[1:]))
    if _normalize_predicate_token(gp) != _normalize_predicate_token(goal_atom[0]):
        return None, "predicate_mismatch"
    if len(ga) != len(ha):
        return None, "arity_mismatch"
    s = subst or Substitution.empty()
    for g, h in zip(ga, ha):
        u = unify_terms(g, h, s)
        if u is None:
            return None, "term_unification_failed"
        s = u
    return s, None
