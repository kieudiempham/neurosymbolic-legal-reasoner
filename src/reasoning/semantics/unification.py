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
from utils.semantic_families import CANONICAL_FAMILIES, normalize_predicate_family
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


_ACTION_OBJECT_RELAXED_FAMILIES = {
    "obligation",
    "permission",
    "prohibition",
    "applicability",
    "legal_effect",
}

_GENERIC_ACTION_OBJECT_TOKENS = {
    "x",
    "y",
    "z",
    "object",
    "action",
    "unknown",
    "doi_tuong",
    "hanh_vi",
    "procedure_or_consequence",
}

_ACTION_OBJECT_NOISE = {
    "co",
    "duoc",
    "phep",
    "phai",
    "bat",
    "buoc",
    "nghia",
    "vu",
    "truong",
    "hop",
    "nao",
    "nhu",
    "the",
    "khi",
    "bao",
    "lau",
    "nhieu",
    "khong",
    "mot",
    "so",
}

_ACTION_GROUP_HINTS = {
    "notification": ("thong_bao", "gui"),
    "registration": ("dang_ky", "cap_nhat"),
    "submission": ("nop", "bo_sung", "ho_so"),
    "payment": ("thue", "le_phi", "tien"),
    "enforcement": ("cuong_che", "xu_phat"),
}

_ACTION_GROUP_CONFLICTS = {
    ("notification", "payment"),
    ("notification", "enforcement"),
    ("notification", "submission"),
    ("registration", "payment"),
    ("registration", "enforcement"),
    ("registration", "submission"),
    ("payment", "notification"),
    ("payment", "registration"),
    ("payment", "submission"),
    ("enforcement", "notification"),
    ("enforcement", "registration"),
    ("enforcement", "submission"),
    ("submission", "notification"),
    ("submission", "registration"),
    ("submission", "payment"),
}

_CANONICAL_PREDICATE_FAMILIES = set(CANONICAL_FAMILIES)


def _is_symbolic_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    t = value.strip()
    if not t:
        return True
    tl = lower_fold(t).replace("-", "_").replace(" ", "_")
    return tl in _GENERIC_ACTION_OBJECT_TOKENS


def _action_object_tokens(value: Any) -> set[str]:
    raw = lower_fold(str(value or "")).replace("_", " ").replace("-", " ")
    toks = [t for t in raw.split() if t]
    return {t for t in toks if len(t) > 1 and t not in _ACTION_OBJECT_NOISE}


def _action_object_equivalent(a: Any, b: Any) -> bool:
    if _is_symbolic_placeholder(a) or _is_symbolic_placeholder(b):
        return True
    if _fuzzy_equal(a, b):
        return True
    ta = _action_object_tokens(a)
    tb = _action_object_tokens(b)
    if not ta or not tb:
        return False
    inter = len(ta & tb)
    union = len(ta | tb)
    if inter == 0:
        return False
    # Require a stronger overlap so generic prefixes like "nop" do not over-unify.
    return (inter / max(1, union) >= 0.45) or (inter >= 2 and inter / max(1, union) >= 0.4)


def _action_group(value: Any) -> str:
    token = _normalize_predicate_token(value)
    if not token:
        return ""
    for group, cues in _ACTION_GROUP_HINTS.items():
        if any(cue in token for cue in cues):
            return group
    return "other"


def _action_group_conflict(goal_action: Any, head_action: Any) -> bool:
    goal_group = _action_group(goal_action)
    head_group = _action_group(head_action)
    if not goal_group or not head_group or goal_group == "other" or head_group == "other":
        return False
    return (goal_group, head_group) in _ACTION_GROUP_CONFLICTS


def _unify_terms_for_slot(
    a: Any,
    b: Any,
    subst: Substitution,
    *,
    relaxed_action_object: bool,
) -> Substitution | None:
    u = unify_terms(a, b, subst)
    if u is not None:
        return u
    if relaxed_action_object and _action_object_equivalent(a, b):
        return subst
    return None


def _normalize_predicate_token(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return ""
    folded = lower_fold(s)
    folded = folded.replace("-", "_").replace(" ", "_")
    while "__" in folded:
        folded = folded.replace("__", "_")
    return folded.strip("_")


def _predicate_family(value: Any) -> str:
    token = _normalize_predicate_token(value)
    if not token:
        return ""
    return normalize_predicate_family(token)


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
    ha = apply_substitution_to_goal_tuple(rr.head_atom, subst)
    pos = apply_substitution_to_conditions(rr.positive_conditions, subst)
    neg = apply_substitution_to_conditions(rr.negative_conditions, subst)
    exc = apply_substitution_to_conditions(rr.exception_conditions, subst)
    cons = tuple(apply_substitution_to_constraint(c, subst) for c in rr.constraints)
    return rr.model_copy(
        update={
            "goal_atom": ga,
            "head_atom": ha,
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
    goal_pred = _normalize_predicate_token(gp)
    head_pred = _normalize_predicate_token(goal_atom[0])
    if goal_pred != head_pred:
        goal_family = _predicate_family(goal_pred)
        head_family = _predicate_family(head_pred)
        if not goal_family or goal_family != head_family:
            return None, "predicate_mismatch"
        goal_action = ga[1] if len(ga) > 1 else None
        head_action = ha[1] if len(ha) > 1 else None
        if _action_group_conflict(goal_action, head_action):
            return None, "action_group_conflict"
    if len(ga) != len(ha):
        return None, "arity_mismatch"
    family = _predicate_family(goal_pred)
    s = subst or Substitution.empty()
    for idx, (g, h) in enumerate(zip(ga, ha)):
        # Slot 0 is subject and remains strict; slots 1.. are action/object and can be relaxed for selected families.
        relaxed_slot = idx >= 1 and family in _ACTION_OBJECT_RELAXED_FAMILIES
        u = _unify_terms_for_slot(g, h, s, relaxed_action_object=relaxed_slot)
        if u is None:
            return None, "term_unification_failed"
        s = u
    return s, None
