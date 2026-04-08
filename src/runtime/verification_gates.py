"""
Active NeSy verification gates: rule → backward → forward must ACCEPT (or repair) before downstream stages.

Policy helpers keep ``qa_orchestrator`` thin; all gates return structured traces for ``debug_trace``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class VerificationLevel(Enum):
    """Three-level verification: only hard rejects block."""
    ACCEPT = "accept"
    SOFT_REJECT = "soft_reject"  # Can proceed with warning
    HARD_REJECT = "hard_reject"  # Must block and try next

from reasoning.backward_reasoner import body_to_requirements, build_backward_plan_only, fact_satisfies_requirement, run_backward
from reasoning.forward_reasoner import run_forward
from reasoning.proof_builder import build_partial_proof, build_proof
from reasoning.requirement_artifact import build_requirement_set_artifact, requirement_missing_fact_keys
from retrieval.rulebase_loader import RulebaseIndex
from rulebase.rule_identity import global_rule_key
from runtime.cross_domain_policy import CrossDomainPolicy
from runtime.reasoning_context import ReasoningContext
from runtime.rule_selection_policy import select_best_candidates_with_policy
from runtime.temporal_policy import rule_temporally_valid
from runtime.conflict_resolution_policy import prune_conflicting_candidates
from schemas.question_parse import Layer2Parse
from schemas.reasoning import ReasoningState
from schemas.rule import RuleRecord
from schemas.session import SessionState
from schemas.verification import VerificationRecord
from verification.engine import NeSyEngine
from verification.repair_loop import run_backward_repair_loop, run_forward_repair_loop, run_rule_repair_loop

logger = logging.getLogger(__name__)


@dataclass
class RuleBackwardGateOutcome:
    """When ``clarification_needed`` is True, caller returns clarification before any forward gate."""

    ok: bool
    clarification_needed: bool = False
    selected: RuleRecord | None = None
    bstate: ReasoningState | None = None
    v_rule: VerificationRecord | None = None
    v_back: VerificationRecord | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    tried_rule_ids: list[str] = field(default_factory=list)
    candidate_verdicts: dict[str, dict[str, Any]] = field(default_factory=dict)  # rule_id -> {level, reason}
    soft_reject_count: int = 0
    hard_reject_count: int = 0


@dataclass
class ForwardGateOutcome:
    ok: bool
    conclusion: str = ""
    goal_achieved: bool = False
    fstate: ReasoningState | None = None
    proof_obj: Any = None
    v_fwd: VerificationRecord | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


def _triage_missing_facts(state: ReasoningState) -> tuple[list[str], list[str]]:
    """Split missing facts into critical vs optional for clarification gating."""
    if state.requirement_artifact is not None:
        return list(state.requirement_artifact.unmet_required), list(state.requirement_artifact.unmet_optional)

    by_key = {req.key: req for req in state.requirement_set}
    critical: list[str] = []
    optional: list[str] = []
    for key in list(state.missing_facts or []):
        req = by_key.get(key)
        kind = (req.requirement_kind or "") if req else ""
        is_critical = False
        if kind in ("negative", "exception", "constraint"):
            is_critical = True
        elif key.startswith("constraint:"):
            is_critical = True
        elif "unless(" in key or "exception_applies(" in key:
            is_critical = True
        if is_critical:
            critical.append(key)
        else:
            optional.append(key)
    return critical, optional


def gate_rule_and_backward(
    engine: NeSyEngine,
    *,
    goal: dict[str, Any],
    layer2: Layer2Parse,
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    known_facts: dict[str, Any],
    rule_index: RulebaseIndex,
    max_rule_repair: int = 2,
    max_backward_repair: int = 1,
    reasoning_context: ReasoningContext | None = None,
    cross_domain_policy: CrossDomainPolicy | None = None,
    structured_facts: dict[str, dict[str, Any]] | None = None,
) -> RuleBackwardGateOutcome:
    """
    For each backward-plan candidate: ``verify_rule`` (with repair), then ``run_backward`` + ``verify_backward``.

    If the chosen path has ``missing_facts``, verification is still recorded but the caller should ask for
    clarification without requiring ``verify_backward`` ACCEPT.

    If there are no missing facts, ``verify_backward`` must end at ACCEPT (after repair), or the next
    candidate is tried.
    """
    out = RuleBackwardGateOutcome(ok=False, clarification_needed=False, selected=None, bstate=None)
    if not ranked:
        out.error = "no_candidates"
        return out

    plan = build_backward_plan_only(
        goal=goal,
        candidates=ranked,
        known_facts=known_facts,
        reasoning_context=reasoning_context,
        cross_domain_policy=cross_domain_policy,
        structured_facts=structured_facts,
    )
    by_id = {r.rule_id: r for r, _, _ in ranked}
    by_gid = {global_rule_key(r): r for r, _, _ in ranked}

    if not plan.candidates and ranked:
        fallback_rule = ranked[0][0]
        reqs = body_to_requirements(fallback_rule)
        missing = [
            req.key
            for req in reqs
            if not fact_satisfies_requirement(
                req.key,
                known_facts,
                structured_facts=structured_facts,
                reasoning_context=reasoning_context,
            )
        ]
        synthetic_state = ReasoningState(
            requirement_set=reqs,
            missing_facts=[],
            selected_rule_ids=[fallback_rule.rule_id],
            derived_facts=[],
            goal_status="open",
            covered_requirements=[],
            can_continue_forward=not missing,
            trace=["backward_plan_empty", "repair:select_top_rule", "repair:rebuild_requirement_set"],
            backward_plan={
                "candidates": [
                    {
                        "rule_id": fallback_rule.rule_id,
                        "global_rule_key": global_rule_key(fallback_rule),
                        "status": "ready" if not missing else "needs_input",
                        "missing_fact_keys": list(missing),
                    }
                ]
            },
            evaluation_hooks={
                "repair_target": "backward_reasoner",
                "repair_action": "select_top_rule_and_rebuild_requirement_set",
            },
        )
        artifact = build_requirement_set_artifact(
            selected_rule=fallback_rule,
            goal_predicate=str(goal.get("predicate") or fallback_rule.head.predicate or "unknown"),
            requirement_items=reqs,
            missing_keys=missing,
        )
        synthetic_state = synthetic_state.model_copy(
            update={
                "requirement_artifact": artifact,
                "missing_facts": requirement_missing_fact_keys(artifact),
                "covered_requirements": list(artifact.satisfied),
                "can_continue_forward": not requirement_missing_fact_keys(artifact),
            }
        )
        out.trace.append(
            {
                "stage": "backward_plan_repair",
                "rule_id": fallback_rule.rule_id,
                "goal": goal,
                "decision": "REPAIR",
                "repair_target": "backward_reasoner",
                "repair_hints": ["select_top_retrieved_rule", "rebuild_requirement_set", "rerun_backward_verification"],
                "repair_applied": True,
                "rerun_stage": "backward_verification",
                "before_after": {
                    "selected_rule_before": None,
                    "selected_rule_after": fallback_rule.rule_id,
                    "proof_before": None,
                    "proof_after": synthetic_state.backward_plan,
                    "verification_before": "no_plan_candidates",
                    "verification_after": "REPAIR",
                },
            }
        )
        logger.info(
            "[backward_repair] plan empty for goal=%s; fallback rule=%s missing=%d",
            goal.get("predicate"),
            fallback_rule.rule_id,
            len(missing),
        )
        sel, st, v_back, btrace = run_backward_repair_loop(
            engine,
            goal=goal,
            selected_rule=fallback_rule,
            bstate=synthetic_state,
            ranked=ranked,
            known_facts=known_facts,
            max_attempts=max_backward_repair,
        )
        out.trace.append(
            {
                "stage": "backward_plan_repair_rerun",
                "initial_rule_id": fallback_rule.rule_id,
                "final_rule_id": sel.rule_id if sel else None,
                "final_decision": v_back.final_decision,
                "repair_history": btrace,
            }
        )
        if v_back.final_decision in ("ACCEPT", "REPAIR") and sel:
            critical_missing, optional_missing = _triage_missing_facts(st)
            if optional_missing:
                out.trace.append(
                    {
                        "stage": "missing_fact_triage",
                        "rule_id": sel.rule_id,
                        "critical_missing": critical_missing,
                        "optional_missing": optional_missing,
                        "decision": "allow_partial_reasoning" if not critical_missing else "needs_clarification",
                    }
                )
            st = st.model_copy(update={"missing_facts": list(critical_missing), "can_continue_forward": (st.can_continue_forward or not critical_missing)})
            out.ok = True
            out.clarification_needed = bool(critical_missing)
            out.selected = sel
            out.bstate = st
            out.v_back = v_back
            out.candidate_verdicts[sel.rule_id] = {
                "rule_id": sel.rule_id,
                "goal": goal,
                "verification_decision": v_back.final_decision,
                "verification_level": VerificationLevel.SOFT_REJECT.value if v_back.final_decision == "REPAIR" else VerificationLevel.ACCEPT.value,
                "rejection_reason": list(v_back.diagnostics),
                "repair_target": "backward_reasoner",
                "repair_hints": ["select_top_retrieved_rule", "rebuild_requirement_set", "rerun_backward_verification"],
                "critical_missing": critical_missing,
                "optional_missing": optional_missing,
            }
            return out

    for cand in plan.candidates:
        rid = cand.rule_id
        rule = by_gid.get(cand.global_rule_key) if cand.global_rule_key else by_id.get(rid)
        if not rule:
            continue
        out.tried_rule_ids.append(rid)

        law_span = str((rule.source_ref_full or rule.source_ref) or "")

        rule, v_rule, rtrace = run_rule_repair_loop(
            engine,
            layer2_goal=goal,
            rule_candidate=rule,
            law_span=law_span,
            legal_frame=layer2.query_rule_candidate or "",
            rule_index=rule_index,
            max_attempts=max_rule_repair,
        )
        out.trace.append(
            {
                "stage": "rule_gate",
                "rule_id": rid,
                "goal": goal,
                "final_decision": v_rule.final_decision,
                "verification_level": (
                    VerificationLevel.ACCEPT.value if v_rule.final_decision == "ACCEPT" else
                    VerificationLevel.SOFT_REJECT.value if v_rule.final_decision == "REPAIR" else
                    VerificationLevel.HARD_REJECT.value
                ),
                "rejection_reason": list(v_rule.diagnostics),
                "repair_target": v_rule.repair_target,
                "repair_hints": list(getattr(v_rule, "repair_hints", []) or ([v_rule.repair_hint] if v_rule.repair_hint else [])),
                "repair_applied": getattr(v_rule, "repair_applied", False),
                "rerun_stage": getattr(v_rule, "rerun_stage", None),
                "repair_history": rtrace,
            }
        )

        level = (
            VerificationLevel.ACCEPT
            if v_rule.final_decision == "ACCEPT"
            else VerificationLevel.SOFT_REJECT
            if v_rule.final_decision == "REPAIR"
            else VerificationLevel.HARD_REJECT
        )
        out.candidate_verdicts[rid] = {
            "rule_id": rid,
            "goal": goal,
            "verification_decision": v_rule.final_decision,
            "verification_level": level.value,
            "rejection_reason": list(v_rule.diagnostics),
            "repair_target": v_rule.repair_target,
            "repair_hints": list(getattr(v_rule, "repair_hints", []) or ([v_rule.repair_hint] if v_rule.repair_hint else [])),
        }
        logger.info(
            "[rule_gate] candidate rule_id=%s goal=%s decision=%s level=%s reasons=%s",
            rid,
            goal.get("predicate"),
            v_rule.final_decision,
            level.value,
            "; ".join(v_rule.diagnostics[:3]),
        )

        if level == VerificationLevel.HARD_REJECT:
            out.hard_reject_count += 1
            continue
        if level == VerificationLevel.SOFT_REJECT:
            out.soft_reject_count += 1

        # ← TEMPORAL RE-CHECK BEFORE APPLY
        if reasoning_context and reasoning_context.question_time:
            ok, reason = rule_temporally_valid(rule, reasoning_context.question_time)
            if not ok:
                out.trace.append({
                    "stage": "temporal_recheck_before_apply",
                    "rule_id": rid,
                    "goal": goal,
                    "verification_level": VerificationLevel.HARD_REJECT.value,
                    "rejected": True,
                    "reason": reason,
                })
                out.hard_reject_count += 1
                continue

        selected, bstate = run_backward(
            goal=goal,
            candidates=ranked,
            known_facts=known_facts,
            preferred_rule_id=rid,
            reasoning_context=reasoning_context,
            cross_domain_policy=cross_domain_policy,
            structured_facts=structured_facts,
        )
        if not selected:
            out.trace.append(
                {
                    "stage": "backward_select",
                    "rule_id": rid,
                    "goal": goal,
                    "verification_level": VerificationLevel.HARD_REJECT.value,
                    "rejected": True,
                    "reason": "backward_reasoner_returned_no_selected_rule",
                }
            )
            out.hard_reject_count += 1
            continue

        sel, st, v_back, btrace = run_backward_repair_loop(
            engine,
            goal=goal,
            selected_rule=selected,
            bstate=bstate,
            ranked=ranked,
            known_facts=known_facts,
            max_attempts=max_backward_repair,
        )
        out.trace.append(
            {
                "stage": "backward_gate",
                "initial_rule_id": rid,
                "final_rule_id": sel.rule_id if sel else None,
                "final_decision": v_back.final_decision,
                "verification_level": (
                    VerificationLevel.ACCEPT.value if v_back.final_decision == "ACCEPT" else
                    VerificationLevel.SOFT_REJECT.value if v_back.final_decision == "REPAIR" else
                    VerificationLevel.HARD_REJECT.value
                ),
                "rejection_reason": list(v_back.diagnostics),
                "repair_target": v_back.repair_target,
                "repair_hints": list(getattr(v_back, "repair_hints", []) or ([v_back.repair_hint] if v_back.repair_hint else [])),
                "repair_applied": getattr(v_back, "repair_applied", False),
                "rerun_stage": getattr(v_back, "rerun_stage", None),
                "repair_history": btrace,
            }
        )
        logger.info(
            "[backward_gate] candidate rule_id=%s final_rule_id=%s goal=%s decision=%s reasons=%s",
            rid,
            sel.rule_id if sel else None,
            goal.get("predicate"),
            v_back.final_decision,
            "; ".join(v_back.diagnostics[:3]),
        )

        if sel and sel.rule_id != rid:
            # ← RE-CHECK TEMPORAL/CONFLICT IF RULE CHANGED BY REPAIR
            if reasoning_context and reasoning_context.question_time:
                ok, reason = rule_temporally_valid(sel, reasoning_context.question_time)
                if not ok:
                    out.trace.append({
                        "stage": "temporal_recheck_after_repair_switch",
                        "rule_id": sel.rule_id,
                        "goal": goal,
                        "verification_level": VerificationLevel.HARD_REJECT.value,
                        "rejected": True,
                        "reason": reason,
                    })
                    out.hard_reject_count += 1
                    continue
            
            law2 = str((sel.source_ref_full or sel.source_ref) or "")
            _, v_rule2, rtrace2 = run_rule_repair_loop(
                engine,
                layer2_goal=goal,
                rule_candidate=sel,
                law_span=law2,
                legal_frame=layer2.query_rule_candidate or "",
                rule_index=rule_index,
                max_attempts=max_rule_repair,
            )
            out.trace.append({"stage": "rule_reverify_after_backward_switch", "repair_history": rtrace2})
            v_rule = v_rule2
            if v_rule2.final_decision == "REJECT":
                out.hard_reject_count += 1
                continue

        if st.missing_facts:
            critical_missing, optional_missing = _triage_missing_facts(st)
            if optional_missing:
                out.trace.append(
                    {
                        "stage": "missing_fact_triage",
                        "rule_id": sel.rule_id if sel else None,
                        "critical_missing": critical_missing,
                        "optional_missing": optional_missing,
                        "decision": "allow_partial_reasoning" if not critical_missing else "needs_clarification",
                    }
                )
            st = st.model_copy(update={"missing_facts": list(critical_missing), "can_continue_forward": (st.can_continue_forward or not critical_missing)})
            out.ok = True
            out.clarification_needed = bool(critical_missing)
            out.selected = sel
            out.bstate = st
            out.v_rule = v_rule
            out.v_back = v_back
            return out

        if v_back.final_decision in ("ACCEPT", "REPAIR") and sel:
            out.ok = True
            out.clarification_needed = False
            out.selected = sel
            out.bstate = st
            out.v_rule = v_rule
            out.v_back = v_back
            return out

    out.error = "reasoning_blocked_by_rule_verification" if out.hard_reject_count >= len(out.tried_rule_ids) else "reasoning_soft_reject_only"
    return out


def gate_forward_reasoning(
    engine: NeSyEngine,
    *,
    goal: dict[str, Any],
    selected: RuleRecord,
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    session: SessionState,
    known_facts: dict[str, Any],
    backward_plan_dict: dict[str, Any],
    backward_state: ReasoningState | None = None,
    max_forward_repair: int = 1,
    reasoning_context: ReasoningContext | None = None,
    cross_domain_policy: CrossDomainPolicy | None = None,
    phase3_proof_context: dict[str, Any] | None = None,
) -> ForwardGateOutcome:
    """Run forward + proof, then ``verify_forward`` with optional repair (re-run forward + rebuild proof)."""
    out = ForwardGateOutcome(ok=False)
    sf = dict(session.structured_facts) if session.structured_facts else None

    candidate_rules: dict[str, RuleRecord] = {}
    for r, _, _ in ranked:
        candidate_rules[r.rule_id] = r
        candidate_rules[global_rule_key(r)] = r

    def _do_forward() -> tuple[str, bool, ReasoningState, Any]:
        # ← TEMPORAL RE-CHECK BEFORE FORWARD APPLY
        if reasoning_context and reasoning_context.question_time:
            ok, reason = rule_temporally_valid(selected, reasoning_context.question_time)
            if not ok:
                out.trace.append({
                    "stage": "temporal_recheck_before_forward",
                    "rule_id": selected.rule_id,
                    "rejected": True,
                    "reason": reason,
                })
                raise ValueError(f"Temporal rejection: {reason}")  # Force retry or fail
        
        conclusion, goal_ok, fstate, _ = run_forward(
            rule=selected,
            known_facts=known_facts,
            goal=goal,
            backward_plan=backward_plan_dict,
            candidates=ranked,
            reasoning_context=reasoning_context,
            cross_domain_policy=cross_domain_policy,
            structured_facts=sf,
            requirement_artifact=(
                backward_state.requirement_artifact.model_dump(mode="json")
                if backward_state and backward_state.requirement_artifact
                else None
            ),
        )
        win_rule = selected
        fr = fstate.forward_result or {}
        if fr.get("global_rule_key"):
            win_rule = candidate_rules.get(str(fr["global_rule_key"]), selected)
        elif fr.get("rule_id"):
            _by_id = {r.rule_id: r for r, _, _ in ranked}
            win_rule = _by_id.get(fr["rule_id"], selected)
        proof = build_proof(
            rule=win_rule,
            used_facts=list(known_facts.keys()),
            conclusion=conclusion,
            forward_result=fstate.forward_result,
            requirement_artifact=(fstate.requirement_artifact.model_dump(mode="json") if fstate.requirement_artifact else None),
            reasoning_context=reasoning_context,
            candidate_rules=candidate_rules,
            phase3_context=phase3_proof_context,
        )
        return conclusion, goal_ok, fstate, proof

    conclusion, goal_ok, fstate, proof = _do_forward()

    conc, gok, fst, pobj, v_fwd, ftrace = run_forward_repair_loop(
        engine,
        goal=goal,
        conclusion=conclusion,
        goal_achieved=goal_ok,
        known_facts=known_facts,
        forward_state=fstate,
        proof_obj=proof,
        forward_retry_fn=_do_forward,
        max_attempts=max_forward_repair,
        requirement_artifact=(fstate.requirement_artifact.model_dump(mode="json") if fstate and fstate.requirement_artifact else None),
        selected_rule_id=selected.rule_id,
    )
    out.trace.extend(ftrace)
    out.v_fwd = v_fwd
    out.conclusion = conc
    out.goal_achieved = gok
    out.fstate = fst
    out.proof_obj = pobj

    if v_fwd.final_decision == "ACCEPT":
        out.ok = True
        return out

    fail_rule = selected
    if fst and fst.forward_result and fst.forward_result.get("rule_id"):
        by_id = {r.rule_id: r for r, _, _ in ranked}
        fail_rule = by_id.get(str(fst.forward_result.get("rule_id")), selected)
    out.proof_obj = build_partial_proof(
        rule=fail_rule,
        used_facts=list(known_facts.keys()),
        conclusion=conc or f"Kết luận tạm thời theo quy tắc {fail_rule.rule_id}: cần làm rõ thêm điều kiện.",
        forward_result=fst.forward_result if fst else None,
        requirement_artifact=(fst.requirement_artifact.model_dump(mode="json") if fst and fst.requirement_artifact else None),
        reasoning_context=reasoning_context,
        candidate_rules=candidate_rules,
        phase3_context=phase3_proof_context,
    )
    out.trace.append(
        {
            "stage": "forward_partial_proof",
            "rule_id": fail_rule.rule_id,
            "failure_reason": (fst.forward_result or {}).get("failure_reason") if fst and fst.forward_result else None,
            "fail_stage": out.proof_obj.fail_stage if out.proof_obj else None,
        }
    )

    out.error = "forward_verification_failed"
    return out
