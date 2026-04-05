"""Backward chaining: structured `BackwardPlan`, unification, top-N candidates (internal schema)."""

from __future__ import annotations

from typing import Any

from schemas.reasoning import ReasoningState, RequirementItem
from schemas.rule import RuleRecord
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.requirements_bridge import reasoning_rule_to_requirement_items
from reasoning.semantics.backward_plan import build_backward_plan, pick_best_rule_record
from reasoning.semantics.plan_models import BackwardPlan
from reasoning.semantics.unification import unify_goal_dict_with_goal_atom


def body_to_requirements(rule: RuleRecord) -> list[RequirementItem]:
    rr = map_rule_record_to_reasoning_rule(rule)
    return reasoning_rule_to_requirement_items(rr)


def goal_unifies_with_goal_atom(goal: dict[str, Any], goal_atom: tuple[Any, ...]) -> bool:
    subst, fail = unify_goal_dict_with_goal_atom(goal, goal_atom)
    return subst is not None


def goal_unifies_with_head(goal: dict[str, Any], rule: RuleRecord) -> bool:
    rr = map_rule_record_to_reasoning_rule(rule)
    return goal_unifies_with_goal_atom(goal, rr.goal_atom)


def fact_satisfies_requirement(req_key: str, known_facts: dict[str, Any]) -> bool:
    """Boundary-level check (string key) — prefer atom pipeline in `semantics.boundary_facts`."""
    for k, v in known_facts.items():
        if v is False:
            continue
        if v is None or v is True:
            if k == req_key:
                return True
            if req_key in k or k in req_key:
                return True
    return False


def run_backward(
    *,
    goal: dict[str, Any],
    candidates: list[tuple[RuleRecord, float, dict[str, Any]]],
    known_facts: dict[str, Any],
    max_paths: int = 3,
    excluded_rule_ids: frozenset[str] | None = None,
    preferred_rule_id: str | None = None,
) -> tuple[RuleRecord | None, ReasoningState]:
    plan = build_backward_plan(
        goal=goal, candidates=candidates, known_facts=known_facts, max_paths=max_paths
    )
    plan_dict = plan.model_dump(mode="json")
    trace: list[str] = [f"backward_plan:{len(plan.candidates)}_candidates"]

    selected = pick_best_rule_record(
        plan,
        candidates,
        excluded_rule_ids=excluded_rule_ids,
        preferred_rule_id=preferred_rule_id,
    )
    if not selected:
        return None, ReasoningState(
            requirement_set=[],
            missing_facts=[],
            selected_rule_ids=[],
            trace=trace + ["no_unifying_rule"],
            can_continue_forward=False,
            backward_plan=plan_dict,
            evaluation_hooks=plan.evaluation.model_dump(mode="json"),
        )

    reqs = body_to_requirements(selected)
    cand = next((c for c in plan.candidates if c.rule_id == selected.rule_id), None)
    missing = list(cand.missing_fact_keys) if cand else []
    covered = [r.key for r in reqs if r.key not in missing]
    can_forward = bool(cand and not missing and cand.status != "blocked")

    st = ReasoningState(
        requirement_set=reqs,
        missing_facts=missing,
        selected_rule_ids=[selected.rule_id],
        derived_facts=[],
        goal_status="open",
        covered_requirements=covered,
        can_continue_forward=can_forward,
        trace=trace + [f"selected {selected.rule_id}", f"missing={len(missing)}", f"status={cand.status if cand else '?'}"] ,
        backward_plan=plan_dict,
        evaluation_hooks=plan.evaluation.model_dump(mode="json"),
    )
    return selected, st


def build_backward_plan_only(
    *,
    goal: dict[str, Any],
    candidates: list[tuple[RuleRecord, float, dict[str, Any]]],
    known_facts: dict[str, Any],
    max_paths: int = 3,
) -> BackwardPlan:
    """Expose plan builder for tests / tooling."""
    return build_backward_plan(goal=goal, candidates=candidates, known_facts=known_facts, max_paths=max_paths)
