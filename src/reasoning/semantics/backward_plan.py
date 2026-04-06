"""Build structured backward plan: unification, classification, scoring, top-N candidates."""

from __future__ import annotations

from typing import Any

from reasoning.internal.codec import serialize_atom
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.internal.models import Atom, ReasoningRule
from reasoning.requirements_bridge import reasoning_rule_to_requirement_items
from reasoning.fact_matching import atom_truth_status_ctx
from reasoning.semantics.boundary_facts import atom_truth_status
from runtime.domain_reasoning_policy import DomainReasoningPolicy, policy_from_context
from reasoning.semantics.constraint_eval import evaluate_constraint
from reasoning.semantics.plan_models import (
    BackwardCandidate,
    BackwardPlan,
    EvaluationHooks,
    MissingAtom,
    MissingConstraintInput,
    MissingExceptionInput,
)
from reasoning.semantics.unification import (
    Substitution,
    apply_substitution_to_reasoning_rule,
    unify_goal_dict_with_goal_atom,
)
from rulebase.rule_identity import global_rule_key
from schemas.rule import RuleRecord


def _exact_head_match_score(goal: dict[str, Any], rr: ReasoningRule) -> float:
    if goal.get("predicate") != rr.goal_atom[0]:
        return 0.0
    ga = list(goal.get("args") or [])
    ha = list(rr.goal_atom[1:])
    if len(ga) != len(ha):
        return 0.2
    n = len(ga)
    if n == 0:
        return 1.0
    hits = sum(1 for g, h in zip(ga, ha) if str(g).strip() == str(h).strip())
    return hits / max(1, n)


def _score_candidate(
    retrieval_score: float,
    exact_head: float,
    subst: Substitution,
    pos_n: int,
    pos_g: int,
    missing_n: int,
    mc: int,
    me: int,
) -> float:
    cov = pos_g / max(1, pos_n)
    bind_bonus = min(1.0, len(subst.mapping) * 0.08)
    return (
        retrieval_score * 0.28
        + exact_head * 22.0
        + cov * 24.0
        + bind_bonus * 6.0
        + (1.0 / (1.0 + missing_n)) * 14.0
        + (1.0 / (1.0 + mc + me)) * 12.0
    )


def _suggest_question_for_atom(atom: Atom, kind: str) -> str:
    s = serialize_atom(atom)
    if atom.predicate == "applies_if":
        return f"Điều kiện áp dụng sau có đúng với tình huống của bạn không: {s} ?"
    if atom.predicate == "unless":
        return f"Ngoại lệ sau có áp dụng không: {s} ?"
    if atom.predicate == "exception_applies":
        return f"Ngoại lệ sau có áp dụng với tình huống của bạn không: {s} ?"
    if kind == "negative":
        return f"Xác nhận điều kiện loại trừ (unless): {s}"
    if kind == "exception":
        return f"Xác nhận ngoại lệ: {s}"
    return f"Vui lòng xác nhận thông tin liên quan: {s}"


def _atom_truth_for_plan(
    atom: Atom,
    known_facts: dict[str, Any],
    structured_facts: dict[str, dict[str, Any]] | None,
    reasoning_context: Any | None,
) -> str:
    if structured_facts is not None or reasoning_context is not None:
        return atom_truth_status_ctx(
            atom,
            known_facts,
            structured_facts=structured_facts,
            reasoning_context=reasoning_context,
            legacy_fuzzy=True,
        )
    return atom_truth_status(atom, known_facts)


def _classify_rule(
    rr: ReasoningRule,
    known_facts: dict[str, Any],
    rule_id: str,
    *,
    structured_facts: dict[str, dict[str, Any]] | None = None,
    reasoning_context: Any | None = None,
) -> tuple[
    list[dict[str, Any]],
    list[MissingAtom],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[MissingConstraintInput],
    list[MissingExceptionInput],
    list[str],
]:
    grounded: list[dict[str, Any]] = []
    missing_atoms: list[MissingAtom] = []
    neg_checks: list[dict[str, Any]] = []
    exc_checks: list[dict[str, Any]] = []
    cons_checks: list[dict[str, Any]] = []
    miss_cons: list[MissingConstraintInput] = []
    miss_exc: list[MissingExceptionInput] = []
    miss_keys: list[str] = []

    for atom in rr.positive_conditions:
        st = _atom_truth_for_plan(atom, known_facts, structured_facts, reasoning_context)
        payload = {"predicate": atom.predicate, "args": list(atom.args), "status": st}
        if st == "true":
            grounded.append(payload)
        else:
            missing_atoms.append(
                MissingAtom(
                    role="positive",
                    atom=atom.model_dump(mode="json"),
                    rule_id=rule_id,
                    expected_type="boolean",
                    question=_suggest_question_for_atom(atom, "positive"),
                )
            )
            miss_keys.append(serialize_atom(atom))

    for atom in rr.negative_conditions:
        st = _atom_truth_for_plan(atom, known_facts, structured_facts, reasoning_context)
        neg_checks.append({"atom": atom.model_dump(mode="json"), "status": st})
        if st == "missing":
            missing_atoms.append(
                MissingAtom(
                    role="unless",
                    atom=atom.model_dump(mode="json"),
                    rule_id=rule_id,
                    expected_type="boolean",
                    question=_suggest_question_for_atom(atom, "negative"),
                )
            )
            miss_keys.append(serialize_atom(atom))

    for atom in rr.exception_conditions:
        st = _atom_truth_for_plan(atom, known_facts, structured_facts, reasoning_context)
        exc_checks.append({"atom": atom.model_dump(mode="json"), "status": st})
        if st == "missing":
            miss_exc.append(
                MissingExceptionInput(
                    atom=atom.model_dump(mode="json"),
                    rule_id=rule_id,
                    question=_suggest_question_for_atom(atom, "exception"),
                )
            )
            miss_keys.append(serialize_atom(atom))

    for c in rr.constraints:
        ev = evaluate_constraint(c, known_facts)
        cons_checks.append({"type": type(c).__name__, "result": ev.model_dump(mode="json")})
        if ev.status == "missing_input":
            sk = ev.session_key or ""
            miss_cons.append(
                MissingConstraintInput(
                    target="threshold" if "Threshold" in type(c).__name__ else type(c).__name__.lower(),
                    constraint_type=type(c).__name__,
                    expected_type="number" if "Threshold" in type(c).__name__ else "string",
                    question=f"Vui lòng bổ sung dữ liệu để đánh giá ràng buộc {type(c).__name__}.",
                    rule_id=rule_id,
                    session_key_hint=sk,
                )
            )
            miss_keys.append(sk)

    return grounded, missing_atoms, neg_checks, exc_checks, cons_checks, miss_cons, miss_exc, miss_keys


def build_backward_plan(
    *,
    goal: dict[str, Any],
    candidates: list[tuple[RuleRecord, float, dict[str, Any]]],
    known_facts: dict[str, Any],
    max_paths: int = 3,
    structured_facts: dict[str, dict[str, Any]] | None = None,
    reasoning_context: Any | None = None,
    domain_policy: DomainReasoningPolicy | None = None,
) -> BackwardPlan:
    goal_atom_list: list[Any] = [goal.get("predicate"), *list(goal.get("args") or [])]
    unified_ok: list[BackwardCandidate] = []
    hooks = EvaluationHooks()
    pol: DomainReasoningPolicy | None = domain_policy or (
        policy_from_context(reasoning_context) if reasoning_context is not None else None
    )

    for rule, rscore, _meta in candidates:
        rr0 = map_rule_record_to_reasoning_rule(rule)
        subst, fail = unify_goal_dict_with_goal_atom(
            goal,
            rr0.goal_atom,
            reasoning_context=reasoning_context,
            rule=rule,
            domain_policy=pol,
        )
        if subst is None:
            hooks.failure_trace.append({"rule_id": rule.rule_id, "reason": fail or "unify"})
            if fail and "domain" in (fail or "").lower():
                hooks.logic_layer_decisions.append(
                    {
                        "kind": "unification_rejected_by_domain",
                        "rule_id": rule.rule_id,
                        "reason": fail,
                    }
                )
            continue

        rr = apply_substitution_to_reasoning_rule(rr0, subst)
        exact = _exact_head_match_score(goal, rr)
        unif_score = min(1.0, exact + 0.15 * len(subst.mapping))

        g, miss_a, neg_c, exc_c, cons_c, miss_co, miss_e, miss_keys = _classify_rule(
            rr,
            known_facts,
            rule.rule_id,
            structured_facts=structured_facts,
            reasoning_context=reasoning_context,
        )
        pos_n = len(rr.positive_conditions)
        pos_g = sum(
            1
            for a in rr.positive_conditions
            if _atom_truth_for_plan(a, known_facts, structured_facts, reasoning_context) == "true"
        )
        missing_n = len(miss_a) + len(miss_e) + len(miss_co)

        total = _score_candidate(
            float(rscore),
            exact,
            subst,
            max(1, pos_n),
            pos_g,
            missing_n,
            len(miss_co),
            len(miss_e),
        )

        status: Any = "ready"
        if miss_a or miss_co or miss_e:
            status = "needs_input"
        neg_block = any(x.get("status") == "true" for x in neg_c)
        if neg_block:
            status = "blocked"

        cand = BackwardCandidate(
            rule_id=rule.rule_id,
            global_rule_key=global_rule_key(rule),
            retrieval_score=float(rscore),
            unification_score=unif_score,
            total_score=total,
            substitution=dict(subst.mapping),
            grounded_atoms=g,
            missing_atoms=miss_a,
            negative_checks=neg_c,
            exception_checks=exc_c,
            constraint_checks=cons_c,
            missing_constraint_inputs=miss_co,
            missing_exception_inputs=miss_e,
            missing_fact_keys=list(dict.fromkeys(miss_keys)),
            status=status,
        )
        unified_ok.append(cand)

    unified_ok.sort(key=lambda c: c.total_score, reverse=True)
    top = unified_ok[:max_paths]
    hooks.goal_achievement_trace = {"goal_atom": goal_atom_list, "n_candidates": len(top)}
    return BackwardPlan(
        goal_atom=goal_atom_list,
        candidates=top,
        substitutions=[c.substitution for c in top if c.substitution],
        evaluation=hooks,
    )


def pick_best_rule_record(
    plan: BackwardPlan,
    candidates: list[tuple[RuleRecord, float, dict[str, Any]]],
    *,
    excluded_rule_ids: frozenset[str] | None = None,
    preferred_rule_id: str | None = None,
) -> RuleRecord | None:
    """Pick a rule from the unified plan. Prefer ``preferred_rule_id`` if it appears in the plan."""
    excluded = excluded_rule_ids or frozenset()
    by_id = {r.rule_id: r for r, _, _ in candidates}
    by_gid = {global_rule_key(r): r for r, _, _ in candidates}

    def _rule_for_candidate(c: BackwardCandidate) -> RuleRecord | None:
        if c.global_rule_key:
            hit = by_gid.get(c.global_rule_key)
            if hit:
                return hit
        return by_id.get(c.rule_id)

    if preferred_rule_id and preferred_rule_id not in excluded:
        c = next((x for x in plan.candidates if x.rule_id == preferred_rule_id), None)
        if c:
            r = _rule_for_candidate(c)
            if r:
                return r
    for c in plan.candidates:
        if c.rule_id in excluded:
            continue
        r = _rule_for_candidate(c)
        if r:
            return r
    return None
