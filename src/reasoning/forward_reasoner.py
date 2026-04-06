"""Forward chaining — layered evaluation via `run_forward_path` / `run_forward_best_path`."""

from __future__ import annotations

from typing import Any

from rulebase.rule_identity import global_rule_key
from schemas.reasoning import ReasoningState, RequirementItem
from schemas.rule import RuleRecord
from reasoning.backward_reasoner import body_to_requirements
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.semantics.forward_engine import run_forward_best_path, run_forward_path
from runtime.domain_reasoning_policy import policy_from_context
from reasoning.semantics.plan_models import BackwardPlan, ForwardPathResult


def _state_from_forward(
    rule: RuleRecord,
    reqs: list[RequirementItem],
    fwd: ForwardPathResult,
    trace: list[str],
) -> ReasoningState:
    derived = [f"derived:{fwd.conclusion}"] if fwd.conclusion else []
    return ReasoningState(
        requirement_set=reqs,
        missing_facts=[],
        selected_rule_ids=[rule.rule_id],
        derived_facts=derived,
        goal_status="satisfied" if fwd.goal_reached else "failed",
        covered_requirements=[r.key for r in reqs],
        can_continue_forward=fwd.goal_reached,
        trace=trace,
        forward_result=fwd.model_dump(mode="json"),
        failure_reason=None if fwd.goal_reached else fwd.failure_reason,
        evaluation_hooks={
            "goal_achievement_trace": {"goal_reached": fwd.goal_reached, "rule_id": fwd.rule_id},
            "constraint_evaluation_trace": [x.model_dump(mode="json") for x in fwd.constraint_traces],
            "failure_trace": [r.model_dump(mode="json") for r in fwd.failed_path_records],
            "failed_rule_ids": list(fwd.failed_paths),
        },
    )


def run_forward(
    *,
    rule: RuleRecord,
    known_facts: dict[str, Any],
    goal: dict[str, Any],
    backward_plan: dict[str, Any] | None = None,
    candidates: list[tuple[RuleRecord, float, dict[str, Any]]] | None = None,
    substitution: dict[str, Any] | None = None,
    reasoning_context: Any | None = None,
    cross_domain_policy: Any | None = None,
    structured_facts: dict[str, dict[str, Any]] | None = None,
) -> tuple[str, bool, ReasoningState, list[str]]:
    """
    If `backward_plan` + `candidates` are set, try candidate paths in order.
    Otherwise evaluate a single `rule` (tests / simple calls).
    """
    trace: list[str] = []

    if backward_plan is not None and candidates is not None:
        cand_use = list(candidates)
        if reasoning_context is not None and cross_domain_policy is not None:
            from runtime.cross_domain_policy import filter_ranked_for_primary_phase

            cand_use, _ = filter_ranked_for_primary_phase(
                cand_use,
                primary_domains=list(reasoning_context.primary_domains),
                include_shared=reasoning_context.include_shared,
            )
        bp = BackwardPlan.model_validate(backward_plan)
        fwd = run_forward_best_path(
            plan=bp,
            candidates=cand_use,
            goal=goal,
            known_facts=known_facts,
            reasoning_context=reasoning_context,
            structured_facts=structured_facts,
        )
        win_rule = next(
            (
                r
                for r, _, _ in cand_use
                if (fwd.global_rule_key and global_rule_key(r) == fwd.global_rule_key)
                or (not fwd.global_rule_key and r.rule_id == fwd.rule_id)
            ),
            rule,
        )
        reqs = body_to_requirements(win_rule)
        st = _state_from_forward(win_rule, reqs, fwd, trace + ["forward_multi_path"])
        return fwd.conclusion, fwd.goal_reached, st, trace

    reqs = body_to_requirements(rule)
    rr = map_rule_record_to_reasoning_rule(rule)
    cand_sub = substitution
    if cand_sub is None:
        from reasoning.semantics.unification import unify_goal_dict_with_goal_atom

        pol = policy_from_context(reasoning_context) if reasoning_context is not None else None
        s, _ = unify_goal_dict_with_goal_atom(
            goal,
            rr.goal_atom,
            reasoning_context=reasoning_context,
            rule=rule,
            domain_policy=pol,
        )
        cand_sub = dict(s.mapping) if s is not None else {}

    fwd = run_forward_path(
        rule=rule,
        goal=goal,
        known_facts=known_facts,
        substitution=cand_sub,
        reasoning_context=reasoning_context,
        structured_facts=structured_facts,
    )
    st = _state_from_forward(rule, reqs, fwd, trace + ["forward_single_path"])
    return fwd.conclusion, fwd.goal_reached, st, trace


def run_forward_path_only(
    *,
    rule: RuleRecord,
    known_facts: dict[str, Any],
    goal: dict[str, Any],
    substitution: dict[str, Any] | None = None,
) -> ForwardPathResult:
    """Direct access for tests."""
    return run_forward_path(rule=rule, goal=goal, known_facts=known_facts, substitution=substitution)
