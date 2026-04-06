"""
Active NeSy verification gates: rule → backward → forward must ACCEPT (or repair) before downstream stages.

Policy helpers keep ``qa_orchestrator`` thin; all gates return structured traces for ``debug_trace``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from reasoning.backward_reasoner import build_backward_plan_only, run_backward
from reasoning.forward_reasoner import run_forward
from reasoning.proof_builder import build_proof
from retrieval.rulebase_loader import RulebaseIndex
from rulebase.rule_identity import global_rule_key
from runtime.cross_domain_policy import CrossDomainPolicy
from runtime.reasoning_context import ReasoningContext
from schemas.question_parse import Layer2Parse
from schemas.reasoning import ReasoningState
from schemas.rule import RuleRecord
from schemas.session import SessionState
from schemas.verification import VerificationRecord
from verification.engine import NeSyEngine
from verification.repair_loop import run_backward_repair_loop, run_forward_repair_loop, run_rule_repair_loop


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
                "final_decision": v_rule.final_decision,
                "repair_history": rtrace,
            }
        )

        if v_rule.final_decision != "ACCEPT":
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
                "repair_history": btrace,
            }
        )

        if sel and sel.rule_id != rid:
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
            if v_rule2.final_decision != "ACCEPT":
                continue

        if st.missing_facts:
            out.ok = True
            out.clarification_needed = True
            out.selected = sel
            out.bstate = st
            out.v_rule = v_rule
            out.v_back = v_back
            return out

        if v_back.final_decision == "ACCEPT" and sel:
            out.ok = True
            out.clarification_needed = False
            out.selected = sel
            out.bstate = st
            out.v_rule = v_rule
            out.v_back = v_back
            return out

    out.error = "reasoning_blocked_by_rule_verification"
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
        conclusion, goal_ok, fstate, _ = run_forward(
            rule=selected,
            known_facts=known_facts,
            goal=goal,
            backward_plan=backward_plan_dict,
            candidates=ranked,
            reasoning_context=reasoning_context,
            cross_domain_policy=cross_domain_policy,
            structured_facts=sf,
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

    out.error = "forward_verification_failed"
    return out
