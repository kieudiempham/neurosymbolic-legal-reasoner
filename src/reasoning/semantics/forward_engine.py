"""Forward evaluation: layered checks, constraint evaluation, typed failures, optional multi-path."""

from __future__ import annotations

from typing import Any

from reasoning.internal.codec import canonicalize_atom, serialize_atom
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.internal.models import Atom
from reasoning.fact_matching import atom_truth_status_ctx
from reasoning.semantics.boundary_facts import atom_truth_status, known_atoms_from_facts
from reasoning.semantics.constraint_eval import evaluate_constraint
from reasoning.semantics.failed_path_hints import failed_path_record_from_result
from reasoning.semantics.plan_models import (
    ConstraintEvaluationResult,
    FailedPathRecord,
    FailureReason,
    ForwardPathResult,
    ProofStepRecord,
)
from reasoning.semantics.unification import (
    Substitution,
    apply_substitution_to_reasoning_rule,
    unify_goal_dict_with_goal_atom,
)
from runtime.domain_reasoning_policy import policy_from_context
from rulebase.rule_identity import global_rule_key
from schemas.rule import RuleRecord


def _supporting_positive_dicts(
    rr: Any,
    known_facts: dict[str, Any],
    structured_facts: dict[str, dict[str, Any]] | None = None,
    reasoning_context: Any | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for a in rr.positive_conditions:
        if _fwd_atom_status(a, known_facts, structured_facts, reasoning_context) == "true":
            out.append(
                {
                    "predicate": a.predicate,
                    "args": list(a.args),
                    "serialized": serialize_atom(canonicalize_atom(a)),
                }
            )
    return out


def _neg_atom_dict(atom: Atom) -> dict[str, Any]:
    return {
        "predicate": atom.predicate,
        "args": list(atom.args),
        "serialized": serialize_atom(canonicalize_atom(atom)),
    }


def _exc_atom_dict(atom: Atom) -> dict[str, Any]:
    return _neg_atom_dict(atom)


def _fwd_atom_status(
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


def run_forward_path(
    *,
    rule: RuleRecord,
    goal: dict[str, Any],
    known_facts: dict[str, Any],
    substitution: dict[str, Any] | None = None,
    reasoning_context: Any | None = None,
    structured_facts: dict[str, dict[str, Any]] | None = None,
) -> ForwardPathResult:
    """Single rule path: positive → negative (unless) → exception → constraints → derive goal."""
    rr0 = map_rule_record_to_reasoning_rule(rule)
    subst = Substitution(mapping=dict(substitution or {}))
    rr = apply_substitution_to_reasoning_rule(rr0, subst)
    goal_atom_list = list(rr.goal_atom)

    if reasoning_context is not None and getattr(reasoning_context, "strict_domain_enforcement", False):
        pol = policy_from_context(reasoning_context)
        ok, rreason = pol.allows_rule(rule, reasoning_context)
        if not ok:
            return ForwardPathResult(
                rule_id=rule.rule_id,
                global_rule_key=global_rule_key(rule),
                goal_reached=False,
                failure_reason="domain_policy_blocked",
                failure_detail=rreason or "domain_policy_blocked",
                substitution=dict(subst.mapping),
                goal_atom=goal_atom_list,
            )

    def _fail(
        fr: FailureReason,
        detail: str,
        *,
        traces: list[ConstraintEvaluationResult],
        known_snap: list[str],
        supporting: list[dict[str, Any]] | None = None,
        blocking_neg: list[dict[str, Any]] | None = None,
        triggered_exc: list[dict[str, Any]] | None = None,
    ) -> ForwardPathResult:
        return ForwardPathResult(
            rule_id=rule.rule_id,
            global_rule_key=global_rule_key(rule),
            goal_reached=False,
            failure_reason=fr,
            failure_detail=detail,
            substitution=dict(subst.mapping),
            constraint_traces=traces,
            known_atoms_snapshot=known_snap,
            goal_atom=goal_atom_list,
            supporting_atoms=supporting
            or _supporting_positive_dicts(rr, known_facts, structured_facts, reasoning_context),
            blocking_negative_atoms=blocking_neg or [],
            triggered_exception_atoms=triggered_exc or [],
        )

    pol_u = policy_from_context(reasoning_context) if reasoning_context is not None else None
    s_goal, ufail = unify_goal_dict_with_goal_atom(
        goal,
        rr.goal_atom,
        reasoning_context=reasoning_context,
        rule=rule,
        domain_policy=pol_u,
    )
    if s_goal is None and subst.mapping:
        # Guard: backward-provided substitution can be stale for this forward attempt.
        # Retry unification against original rule head to reduce false unification_broken.
        s_retry, _retry_fail = unify_goal_dict_with_goal_atom(
            goal,
            rr0.goal_atom,
            reasoning_context=reasoning_context,
            rule=rule,
            domain_policy=pol_u,
        )
        if s_retry is not None:
            rr = apply_substitution_to_reasoning_rule(rr0, s_retry)
            goal_atom_list = list(rr.goal_atom)
            s_goal = s_retry
            ufail = None
    if s_goal is None:
        return ForwardPathResult(
            rule_id=rule.rule_id,
            global_rule_key=global_rule_key(rule),
            goal_reached=False,
            failure_reason="unification_broken",
            failure_detail=ufail or "goal_does_not_unify_with_head",
            substitution=dict(subst.mapping),
            goal_atom=goal_atom_list,
        )

    traces: list[ConstraintEvaluationResult] = []
    known_snap = [serialize_atom(a) for a, _v in known_atoms_from_facts(known_facts)]

    for atom in rr.positive_conditions:
        st = _fwd_atom_status(atom, known_facts, structured_facts, reasoning_context)
        if st != "true":
            return _fail(
                "positive_condition_missing",
                serialize_atom(canonicalize_atom(atom)),
                traces=traces,
                known_snap=known_snap,
                supporting=_supporting_positive_dicts(rr, known_facts, structured_facts, reasoning_context),
            )

    supporting = _supporting_positive_dicts(rr, known_facts, structured_facts, reasoning_context)

    for atom in rr.negative_conditions:
        st = _fwd_atom_status(atom, known_facts, structured_facts, reasoning_context)
        if st == "true":
            return _fail(
                "negative_condition_blocked",
                serialize_atom(canonicalize_atom(atom)),
                traces=traces,
                known_snap=known_snap,
                supporting=supporting,
                blocking_neg=[_neg_atom_dict(atom)],
            )
        if st == "missing":
            return _fail(
                "unless_condition_unknown",
                serialize_atom(canonicalize_atom(atom)),
                traces=traces,
                known_snap=known_snap,
                supporting=supporting,
            )

    for atom in rr.exception_conditions:
        st = _fwd_atom_status(atom, known_facts, structured_facts, reasoning_context)
        if st == "true":
            return _fail(
                "exception_triggered",
                serialize_atom(canonicalize_atom(atom)),
                traces=traces,
                known_snap=known_snap,
                supporting=supporting,
                triggered_exc=[_exc_atom_dict(atom)],
            )
        if st == "missing":
            return _fail(
                "exception_unknown",
                serialize_atom(canonicalize_atom(atom)),
                traces=traces,
                known_snap=known_snap,
                supporting=supporting,
            )

    for c in rr.constraints:
        ev = evaluate_constraint(c, known_facts)
        traces.append(ev)
        if ev.status == "failed":
            return _fail(
                "constraint_failed",
                ev.detail,
                traces=traces,
                known_snap=known_snap,
                supporting=supporting,
            )
        if ev.status == "missing_input":
            return _fail(
                "constraint_missing_input",
                ev.session_key,
                traces=traces,
                known_snap=known_snap,
                supporting=supporting,
            )
        if ev.status == "unknown":
            return _fail(
                "constraint_unknown",
                ev.detail,
                traces=traces,
                known_snap=known_snap,
                supporting=supporting,
            )

    ga = rr.goal_atom
    atom = Atom(predicate=str(ga[0]), args=tuple(ga[1:]))
    conclusion = serialize_atom(canonicalize_atom(atom))
    derived = [conclusion]

    proof = ProofStepRecord(
        derived_atom=list(ga),
        rule_id=rule.rule_id,
        supporting_atoms=[list(x.args) for x in rr.positive_conditions],
        negative_checks=[{"atom": x.model_dump(mode="json")} for x in rr.negative_conditions],
        exception_checks=[{"atom": x.model_dump(mode="json")} for x in rr.exception_conditions],
        applied_constraints=[{"type": type(c).__name__} for c in rr.constraints],
        substitution=dict(subst.mapping),
        status="ok",
    )

    return ForwardPathResult(
        rule_id=rule.rule_id,
        global_rule_key=global_rule_key(rule),
        goal_reached=True,
        conclusion=conclusion,
        failure_reason="none",
        substitution=dict(subst.mapping),
        proof_steps=[proof],
        constraint_traces=traces,
        derived_atoms=derived,
        known_atoms_snapshot=known_snap,
        goal_atom=goal_atom_list,
        supporting_atoms=supporting,
        blocking_negative_atoms=[
            _neg_atom_dict(a)
            for a in rr.negative_conditions
            if _fwd_atom_status(a, known_facts, structured_facts, reasoning_context) == "false"
        ],
    )


def run_forward_best_path(
    *,
    plan: Any,
    candidates: list[tuple[RuleRecord, float, dict[str, Any]]],
    goal: dict[str, Any],
    known_facts: dict[str, Any],
    reasoning_context: Any | None = None,
    structured_facts: dict[str, dict[str, Any]] | None = None,
) -> ForwardPathResult:
    """Try candidate paths in plan order until one reaches the goal."""
    from reasoning.semantics.plan_models import BackwardPlan

    bp = plan if isinstance(plan, BackwardPlan) else BackwardPlan.model_validate(plan)
    by_id = {r.rule_id: r for r, _, _ in candidates}
    by_gid = {global_rule_key(r): r for r, _, _ in candidates}
    failed_records: list[FailedPathRecord] = []
    last: ForwardPathResult | None = None
    for c in bp.candidates:
        if c.unification_failure:
            continue
        rule = by_gid.get(c.global_rule_key) if c.global_rule_key else by_id.get(c.rule_id)
        if not rule:
            continue
        res = run_forward_path(
            rule=rule,
            goal=goal,
            known_facts=known_facts,
            substitution=c.substitution,
            reasoning_context=reasoning_context,
            structured_facts=structured_facts,
        )
        last = res
        if res.goal_reached:
            res.failed_path_records = failed_records
            return res
        failed_records.append(failed_path_record_from_result(rule, res, goal=goal))
    if last:
        last.failed_path_records = failed_records
        if not last.goal_reached and last.failure_reason == "none":
            last.failure_reason = "goal_not_derived"
        return last
    return ForwardPathResult(
        rule_id="",
        global_rule_key="",
        goal_reached=False,
        failure_reason="goal_not_derived",
        failure_detail="no_candidate_paths",
        failed_path_records=failed_records,
    )


def forward_agenda_fixed_point(
    *,
    rule: RuleRecord,
    goal: dict[str, Any],
    known_facts: dict[str, Any],
    substitution: dict[str, Any] | None = None,
    max_rounds: int = 4,
) -> ForwardPathResult:
    """
    Thin fixed-point wrapper: re-run path evaluation until stable or cap.
    (Single-rule base case is stable in one round; hook for future multi-rule expansion.)
    """
    last = run_forward_path(rule=rule, goal=goal, known_facts=known_facts, substitution=substitution)
    for _ in range(1, max_rounds):
        if last.goal_reached:
            break
        nxt = run_forward_path(rule=rule, goal=goal, known_facts=known_facts, substitution=substitution)
        if nxt.model_dump() == last.model_dump():
            break
        last = nxt
    return last
