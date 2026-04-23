"""Backward chaining: structured `BackwardPlan`, unification, top-N candidates (internal schema)."""

from __future__ import annotations

from typing import Any

from rulebase.rule_identity import global_rule_key
from reasoning.fact_matching import fact_satisfies_requirement_ctx
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.requirements_bridge import reasoning_rule_to_requirement_items
from reasoning.requirement_artifact import build_requirement_set_artifact, requirement_missing_fact_keys
from reasoning.semantics.backward_plan import build_backward_plan
from reasoning.semantics.backward_plan import pick_best_rule_record
from reasoning.semantics.plan_models import BackwardCandidate, BackwardPlan, EvaluationHooks
from reasoning.semantics.unification import Substitution, apply_substitution_to_reasoning_rule, unify_goal_dict_with_goal_atom
from schemas.reasoning import ReasoningState, RequirementItem
from schemas.rule import RuleRecord
from runtime.rule_selection_policy import select_best_candidates_with_policy
from utils.semantic_families import normalize_predicate_family


def _semantic_family(value: Any) -> str:
    return normalize_predicate_family(value)


def _is_variable_like(token: Any) -> bool:
    t = str(token or "").strip()
    if not t:
        return False
    if t.startswith("?") or t in {"_", "*"} or t.upper().startswith("VAR"):
        return True
    return t.isalpha() and t.upper() == t and len(t) <= 3


def _subject_strict_compatible(goal: dict[str, Any], rule: RuleRecord) -> bool:
    ga = list(goal.get("args") or [])
    ha = list((rule.head.args if rule.head else []) or [])
    if not ga or not ha:
        return True
    gs = str(ga[0]).strip().lower()
    hs = str(ha[0]).strip().lower()
    if gs == hs:
        return True
    return _is_variable_like(ha[0])


def _rescued_backward_admission_reason(goal: dict[str, Any], rule: RuleRecord) -> str | None:
    head_pred = str(rule.head.predicate if rule.head else "").strip()
    if not head_pred:
        return None
    goal_pred = str(goal.get("predicate") or "").strip()
    goal_family = _semantic_family(goal_pred)
    head_family = _semantic_family(head_pred)
    logic_family = _semantic_family(getattr(rule, "logic_form", ""))
    if not _subject_strict_compatible(goal, rule):
        return None
    if goal_pred and goal_pred == head_pred:
        return "head_predicate_exact_with_subject_strict"
    if goal_family and head_family and goal_family == head_family:
        return "semantic_family_head_compatible_subject_strict"
    if goal_family and logic_family and goal_family == logic_family:
        return "semantic_family_logic_form_compatible_subject_strict"
    return None


def _synthesize_rescued_candidate(
    goal: dict[str, Any],
    rule: RuleRecord,
    retrieval_score: float,
    known_facts: dict[str, Any],
    *,
    structured_facts: dict[str, dict[str, Any]] | None,
    reasoning_context: Any | None,
) -> BackwardCandidate:
    reqs = _body_to_requirements_with_substitution(rule, None)
    missing_raw = [
        req.key
        for req in reqs
        if not fact_satisfies_requirement(
            req.key,
            known_facts,
            structured_facts=structured_facts,
            reasoning_context=reasoning_context,
        )
    ]
    status = "ready" if not missing_raw else "needs_input"
    return BackwardCandidate(
        rule_id=rule.rule_id,
        global_rule_key=global_rule_key(rule),
        retrieval_score=float(retrieval_score),
        unification_score=0.0,
        total_score=float(retrieval_score),
        substitution={},
        grounded_atoms=[],
        missing_atoms=[],
        negative_checks=[],
        exception_checks=[],
        constraint_checks=[],
        missing_constraint_inputs=[],
        missing_exception_inputs=[],
        missing_fact_keys=list(dict.fromkeys(missing_raw)),
        status=status,
        unification_failure="rescued_fallback_seeded_candidate",
        rule_head_predicate=str(rule.head.predicate if rule.head else ""),
        rule_logic_form=str(getattr(rule, "logic_form", "") or ""),
        semantic_compatibility=0.0,
        shared_generic_candidate=False,
        weak_grounding=False,
        grounding_reasons=["rescued_fallback_backward_plan_seed"],
    )


def body_to_requirements(rule: RuleRecord) -> list[RequirementItem]:
    rr = map_rule_record_to_reasoning_rule(rule)
    return reasoning_rule_to_requirement_items(rr)


def _body_to_requirements_with_substitution(
    rule: RuleRecord,
    substitution: dict[str, Any] | None,
) -> list[RequirementItem]:
    rr = map_rule_record_to_reasoning_rule(rule)
    if substitution:
        rr = apply_substitution_to_reasoning_rule(rr, Substitution(mapping=dict(substitution)))
    return reasoning_rule_to_requirement_items(rr)


def goal_unifies_with_goal_atom(goal: dict[str, Any], goal_atom: tuple[Any, ...]) -> bool:
    subst, fail = unify_goal_dict_with_goal_atom(goal, goal_atom)
    return subst is not None


def goal_unifies_with_head(goal: dict[str, Any], rule: RuleRecord) -> bool:
    rr = map_rule_record_to_reasoning_rule(rule)
    return goal_unifies_with_goal_atom(goal, rr.goal_atom)


def fact_satisfies_requirement(
    req_key: str,
    known_facts: dict[str, Any],
    *,
    structured_facts: dict[str, dict[str, Any]] | None = None,
    reasoning_context: Any | None = None,
) -> bool:
    """Schema-aware when structured_facts/context provided; else legacy key match."""
    if structured_facts is not None or reasoning_context is not None:
        return fact_satisfies_requirement_ctx(
            req_key,
            known_facts,
            structured_facts=structured_facts,
            reasoning_context=reasoning_context,
        )
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
    admission_source: str | None = None,
    semantic_guard_fallback_rescued: bool = False,
    rule_gate_fallback_relaxed: bool = False,
    reasoning_context: Any | None = None,
    cross_domain_policy: Any | None = None,
    structured_facts: dict[str, dict[str, Any]] | None = None,
) -> tuple[RuleRecord | None, ReasoningState]:
    cand_in = list(candidates)
    if reasoning_context is not None and cross_domain_policy is not None:
        from runtime.cross_domain_policy import filter_ranked_for_primary_phase

        cand_in, _rej = filter_ranked_for_primary_phase(
            cand_in,
            primary_domains=list(reasoning_context.primary_domains),
            include_shared=reasoning_context.include_shared,
        )
    plan = build_backward_plan(
        goal=goal,
        candidates=cand_in,
        known_facts=known_facts,
        max_paths=max_paths,
        structured_facts=structured_facts,
        reasoning_context=reasoning_context,
    )
    rescue_meta: dict[str, Any] = {
        "eligible": False,
        "triggered": False,
        "admission_source": str(admission_source or "planner"),
        "semantic_guard_fallback_rescued": bool(semantic_guard_fallback_rescued),
        "rule_gate_fallback_relaxed": bool(rule_gate_fallback_relaxed),
        "original_candidate_count": len(plan.candidates),
        "rescued_candidate_count": len(plan.candidates),
        "admission_reason": None,
        "final_selected_rule_id": None,
    }

    rescue_eligible = (
        admission_source == "fallback_top_retrieved"
        and bool(semantic_guard_fallback_rescued)
        and bool(rule_gate_fallback_relaxed)
        and bool(preferred_rule_id)
    )
    rescue_meta["eligible"] = rescue_eligible

    preferred_tuple = next(
        (
            (r, float(score), meta if isinstance(meta, dict) else {})
            for r, score, meta in cand_in
            if str(r.rule_id) == str(preferred_rule_id)
        ),
        None,
    )

    if len(plan.candidates) == 0 and rescue_eligible and preferred_tuple is not None:
        preferred_rule, preferred_score, preferred_meta = preferred_tuple
        admission_reason = _rescued_backward_admission_reason(goal, preferred_rule)
        rescue_meta["admission_reason"] = admission_reason
        if admission_reason:
            rescued_goal = dict(goal)
            rescued_goal["predicate"] = str(preferred_rule.head.predicate if preferred_rule.head else goal.get("predicate") or "")
            rescued_plan = build_backward_plan(
                goal=rescued_goal,
                candidates=[preferred_tuple],
                known_facts=known_facts,
                max_paths=max_paths,
                structured_facts=structured_facts,
                reasoning_context=reasoning_context,
            )
            if len(rescued_plan.candidates) == 0:
                synth = _synthesize_rescued_candidate(
                    rescued_goal,
                    preferred_rule,
                    preferred_score,
                    known_facts,
                    structured_facts=structured_facts,
                    reasoning_context=reasoning_context,
                )
                rescued_plan = BackwardPlan(
                    goal_atom=[rescued_goal.get("predicate"), *list(rescued_goal.get("args") or [])],
                    candidates=[synth],
                    substitutions=[],
                    evaluation=EvaluationHooks(
                        goal_achievement_trace={
                            "goal_atom": [rescued_goal.get("predicate"), *list(rescued_goal.get("args") or [])],
                            "n_candidates": 1,
                            "rescued_fallback_seed": True,
                        },
                        failure_trace=list((plan.evaluation.failure_trace if plan and plan.evaluation else []) or []),
                        logic_layer_decisions=list((plan.evaluation.logic_layer_decisions if plan and plan.evaluation else []) or []),
                    ),
                )
            rescue_meta["triggered"] = True
            rescue_meta["rescued_candidate_count"] = len(rescued_plan.candidates)
            rescue_meta["rescued_goal_predicate"] = rescued_goal.get("predicate")
            rescue_meta["rescued_rule_id"] = preferred_rule.rule_id
            rescue_meta["rescued_score_components"] = dict(preferred_meta.get("score_components") or {})
            plan = rescued_plan

    plan_dict = plan.model_dump(mode="json")
    trace: list[str] = [f"backward_plan:{len(plan.candidates)}_candidates"]
    if rescue_meta.get("triggered"):
        trace.append(
            "backward_plan_rescue_triggered:"
            f"{rescue_meta.get('admission_reason') or 'fallback_compatibility'}"
        )

    selected = pick_best_rule_record(
        plan,
        cand_in,
        excluded_rule_ids=excluded_rule_ids,
        preferred_rule_id=preferred_rule_id,
    )
    if selected is None and rescue_meta.get("triggered") and preferred_tuple is not None:
        selected = preferred_tuple[0]
    rescue_meta["final_selected_rule_id"] = selected.rule_id if selected else None
    eval_hooks = plan.evaluation.model_dump(mode="json")
    eval_hooks["backward_plan_rescue"] = rescue_meta
    if not selected:
        return None, ReasoningState(
            requirement_set=[],
            missing_facts=[],
            selected_rule_ids=[],
            requirement_artifact=None,
            trace=trace + ["no_unifying_rule"],
            can_continue_forward=False,
            backward_plan=plan_dict,
            evaluation_hooks=eval_hooks,
        )

    cand = next(
        (
            c
            for c in plan.candidates
            if (c.global_rule_key and c.global_rule_key == global_rule_key(selected))
            or (not c.global_rule_key and c.rule_id == selected.rule_id)
        ),
        None,
    )
    reqs = _body_to_requirements_with_substitution(selected, (cand.substitution if cand else None))
    if cand:
        missing_raw = list(cand.missing_fact_keys)
    else:
        missing_raw = [
            req.key
            for req in reqs
            if not fact_satisfies_requirement(
                req.key,
                known_facts,
                structured_facts=structured_facts,
                reasoning_context=reasoning_context,
            )
        ]
    artifact = build_requirement_set_artifact(
        selected_rule=selected,
        goal_predicate=str(goal.get("predicate") or ""),
        requirement_items=reqs,
        missing_keys=missing_raw,
    )
    missing = requirement_missing_fact_keys(artifact)
    covered = list(artifact.satisfied)
    can_forward = bool(cand and not artifact.unmet_required and not artifact.unmet_optional and cand.status != "blocked")

    st = ReasoningState(
        requirement_set=reqs,
        missing_facts=missing,
        selected_rule_ids=[selected.rule_id],
        requirement_artifact=artifact,
        derived_facts=[],
        goal_status="open",
        covered_requirements=covered,
        can_continue_forward=can_forward,
        trace=trace + [f"selected {selected.rule_id}", f"missing={len(missing)}", f"status={cand.status if cand else '?'}"] ,
        backward_plan=plan_dict,
        evaluation_hooks=eval_hooks,
    )
    return selected, st


def build_backward_plan_only(
    *,
    goal: dict[str, Any],
    candidates: list[tuple[RuleRecord, float, dict[str, Any]]],
    known_facts: dict[str, Any],
    max_paths: int = 3,
    reasoning_context: Any | None = None,
    cross_domain_policy: Any | None = None,
    structured_facts: dict[str, dict[str, Any]] | None = None,
    question_mode: str = "hybrid",
) -> BackwardPlan:
    """Expose plan builder for tests / tooling."""
    cand_in = list(candidates)
    if reasoning_context is not None and cross_domain_policy is not None:
        from runtime.cross_domain_policy import filter_ranked_for_primary_phase

        cand_in, _ = filter_ranked_for_primary_phase(
            cand_in,
            primary_domains=list(reasoning_context.primary_domains),
            include_shared=reasoning_context.include_shared,
        )
    
    # ← METADATA-AWARE SELECTION WITH POLICY
    if reasoning_context and reasoning_context.question_time:
        cand_in = select_best_candidates_with_policy(
            candidates=cand_in,
            question_time=reasoning_context.question_time,
        )
    
    return build_backward_plan(
        goal=goal,
        candidates=cand_in,
        known_facts=known_facts,
        max_paths=max_paths,
        structured_facts=structured_facts,
        reasoning_context=reasoning_context,
        question_mode=question_mode,
    )
