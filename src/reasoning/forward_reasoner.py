"""Forward chaining — layered evaluation via `run_forward_path` / `run_forward_best_path`."""

from __future__ import annotations

from typing import Any

from rulebase.rule_identity import global_rule_key
from schemas.reasoning import ReasoningState, RequirementItem
from schemas.rule import RuleRecord
from reasoning.backward_reasoner import body_to_requirements
from reasoning.requirement_artifact import build_requirement_set_artifact
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.semantics.forward_engine import assess_forward_runtime_quality, run_forward_best_path, run_forward_path
from runtime.domain_reasoning_policy import policy_from_context
from reasoning.semantics.plan_models import BackwardPlan, ForwardPathResult
from runtime.temporal_policy import rule_temporally_valid


def _state_from_forward(
    rule: RuleRecord,
    reqs: list[RequirementItem],
    fwd: ForwardPathResult,
    trace: list[str],
    base_requirement_artifact: dict[str, Any] | None = None,
) -> ReasoningState:
    derived = [f"derived:{fwd.conclusion}"] if fwd.conclusion else []
    missing_keys: list[str] = []
    if not fwd.goal_reached:
        detail = fwd.failure_detail
        if isinstance(detail, list):
            missing_keys = [str(x) for x in detail if str(x).strip()]
        elif detail is not None and str(detail).strip():
            missing_keys = [str(detail)]
    artifact = build_requirement_set_artifact(
        selected_rule=rule,
        goal_predicate=str(fwd.goal_atom[0] if fwd.goal_atom else rule.head.predicate),
        requirement_items=reqs,
        missing_keys=missing_keys,
    )
    if base_requirement_artifact:
        merged_missing = list(base_requirement_artifact.get("unmet_required") or [])
        merged_optional = list(base_requirement_artifact.get("unmet_optional") or [])
        for key in artifact.unmet_required:
            if key not in merged_missing:
                merged_missing.append(key)
        for key in artifact.unmet_optional:
            if key not in merged_optional:
                merged_optional.append(key)
        merged_satisfied = [
            k for k in list(base_requirement_artifact.get("satisfied") or []) if k not in set(merged_missing + merged_optional)
        ]
        artifact = artifact.model_copy(
            update={
                "unmet_required": merged_missing,
                "unmet_optional": merged_optional,
                "satisfied": merged_satisfied,
            }
        )

    missing_facts = list(artifact.unmet_required)
    return ReasoningState(
        requirement_set=reqs,
        missing_facts=missing_facts,
        selected_rule_ids=[rule.rule_id],
        derived_facts=derived,
        goal_status="satisfied" if fwd.goal_reached else "failed",
        covered_requirements=list(artifact.satisfied),
        requirement_artifact=artifact,
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
    requirement_artifact: dict[str, Any] | None = None,
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

        # Part B: Temporal re-check before forward apply
        question_time = getattr(reasoning_context, 'question_time', None) if reasoning_context else None
        if question_time:
            temporal_valid_candidates = []
            for r, score, meta in cand_use:
                if rule_temporally_valid(r, question_time):
                    temporal_valid_candidates.append((r, score, meta))
                else:
                    trace.append(f"temporal_reject_forward: {r.rule_id} at {question_time}")
            if temporal_valid_candidates:
                cand_use = temporal_valid_candidates
            else:
                # If all candidates rejected, keep original but log
                trace.append("temporal_reject_forward: all candidates rejected, proceeding with original")

        quality_rejected: list[tuple[str, str, str]] = []
        quality_eligible: list[tuple[RuleRecord, float, dict[str, Any]]] = []
        for r, score, meta in cand_use:
            ok_q, q_reason, q_detail = assess_forward_runtime_quality(r, goal)
            if ok_q:
                quality_eligible.append((r, score, meta))
            else:
                quality_rejected.append((r.rule_id, str(q_reason or "forward_quality_reject"), q_detail))
                trace.append(f"forward_quality_reject:{r.rule_id}:{q_reason}:{q_detail}")
        if quality_eligible:
            cand_use = quality_eligible
        else:
            reason = quality_rejected[0][1] if quality_rejected else "goal_not_derived"
            detail = quality_rejected[0][2] if quality_rejected else "no_forward_eligible_candidate"
            reqs = body_to_requirements(rule)
            fwd = ForwardPathResult(
                rule_id=rule.rule_id,
                global_rule_key=global_rule_key(rule),
                goal_reached=False,
                failure_reason=reason,
                failure_detail=detail,
                goal_atom=[str(goal.get("predicate") or "unknown"), *list(goal.get("args") or [])],
            )
            st = _state_from_forward(
                rule,
                reqs,
                fwd,
                trace + ["forward_quality_gate_blocked"],
                base_requirement_artifact=requirement_artifact,
            )
            return "", False, st, trace

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
        st = _state_from_forward(
            win_rule,
            reqs,
            fwd,
            trace + ["forward_multi_path"],
            base_requirement_artifact=requirement_artifact,
        )
        return fwd.conclusion, fwd.goal_reached, st, trace

    reqs = body_to_requirements(rule)
    ok_q, q_reason, q_detail = assess_forward_runtime_quality(rule, goal)
    if not ok_q:
        fwd = ForwardPathResult(
            rule_id=rule.rule_id,
            global_rule_key=global_rule_key(rule),
            goal_reached=False,
            failure_reason=str(q_reason or "goal_not_derived"),
            failure_detail=q_detail,
            goal_atom=[str(goal.get("predicate") or "unknown"), *list(goal.get("args") or [])],
        )
        st = _state_from_forward(
            rule,
            reqs,
            fwd,
            trace + ["forward_quality_gate_single"],
            base_requirement_artifact=requirement_artifact,
        )
        return "", False, st, trace

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

    # Part B: Temporal re-check before forward apply (single path)
    question_time = getattr(reasoning_context, 'question_time', None) if reasoning_context else None
    if question_time and not rule_temporally_valid(rule, question_time):
        trace.append(f"temporal_reject_forward_single: {rule.rule_id} at {question_time}")
        # Still proceed but log rejection

    fwd = run_forward_path(
        rule=rule,
        goal=goal,
        known_facts=known_facts,
        substitution=cand_sub,
        reasoning_context=reasoning_context,
        structured_facts=structured_facts,
    )
    st = _state_from_forward(
        rule,
        reqs,
        fwd,
        trace + ["forward_single_path"],
        base_requirement_artifact=requirement_artifact,
    )
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
