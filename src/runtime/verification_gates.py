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

from reasoning.backward_reasoner import build_backward_plan_only, run_backward, body_to_requirements, fact_satisfies_requirement
from reasoning.forward_reasoner import run_forward
from reasoning.proof_builder import build_partial_proof, build_proof
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
from utils.semantic_families import normalize_predicate_family
from utils.text import lower_fold
from verification.engine import NeSyEngine
from verification.repair_loop import run_backward_repair_loop, run_forward_repair_loop, run_rule_repair_loop

logger = logging.getLogger(__name__)


def _semantic_family(value: Any) -> str:
    return normalize_predicate_family(value)


def _rule_semantic_blob(rule: RuleRecord | None) -> str:
    if rule is None:
        return ""
    md = rule.metadata or {}
    prov = md.get("provenance") or {}
    parts = [
        str(rule.logic_form or ""),
        str(rule.head.predicate if rule.head else ""),
        " ".join(str(x or "") for x in (rule.head.args if rule.head else []) or []),
        " ".join(str((x or {}).get("predicate") or "") for x in (rule.body or [])),
        str(md.get("domain") or ""),
        str(md.get("layer") or ""),
        str(md.get("source_doc") or ""),
        str(md.get("source_article") or ""),
        str(prov.get("source_ref_full") or ""),
        str(prov.get("source_ref") or ""),
        str(prov.get("surface_text") or ""),
    ]
    return lower_fold(" ".join(part for part in parts if part))


def _rule_has_anchor(rule: RuleRecord | None, cues: tuple[str, ...]) -> bool:
    blob = _rule_semantic_blob(rule)
    if not blob:
        return False
    return any(cue in blob for cue in cues)


def _semantic_soft_match_info(
    *,
    goal: dict[str, Any] | None,
    rule: RuleRecord | None,
) -> tuple[bool, str, dict[str, Any]]:
    goal_family = _semantic_family((goal or {}).get("predicate"))
    rule_head_family = _semantic_family(rule.head.predicate if rule and rule.head else "")
    rule_logic_family = _semantic_family(getattr(rule, "logic_form", "") if rule else "")
    candidate_families = [f for f in (rule_head_family, rule_logic_family) if f]

    meta = {
        "goal_family": goal_family,
        "rule_head_family": rule_head_family,
        "rule_logic_family": rule_logic_family,
    }
    if not goal_family or not candidate_families:
        return False, "missing_semantic_family", meta

    if goal_family in candidate_families:
        return True, "same_family", meta

    if goal_family == "legal_effect" and any(f in {"obligation", "prohibition"} for f in candidate_families):
        if _rule_has_anchor(rule, ("sanction", "xu_phat", "phat", "vo_hieu", "hieu_luc", "ket_qua", "hau_qua")):
            return True, "legal_effect_related_family", meta

    if goal_family in {"obligation", "prohibition"} and "legal_effect" in candidate_families:
        if _rule_has_anchor(rule, ("sanction", "xu_phat", "phat", "vo_hieu", "hieu_luc", "ket_qua", "hau_qua")):
            return True, "legal_effect_related_family", meta

    if goal_family == "permission" and "obligation" in candidate_families:
        if _rule_has_anchor(rule, ("duoc_phep", "co_quyen", "permission", "allow", "permit")) and _rule_has_anchor(
            rule,
            ("phai", "must", "nghia_vu", "obligation"),
        ):
            return True, "permission_obligation_inverse", meta

    return False, "unrelated_family", meta


def _semantic_match_tier(
    *,
    goal: dict[str, Any] | None,
    rule: RuleRecord | None,
) -> tuple[str, float, str, dict[str, Any]]:
    """Return semantic tier and scoring hint: exact > soft > mismatch."""
    ok, reason, meta = _semantic_soft_match_info(goal=goal, rule=rule)
    if ok and reason == "same_family":
        return "exact", 2.0, reason, meta
    if ok:
        return "soft", 1.0, reason, meta
    return "mismatch", -2.0, reason, meta


def _repair_material_gain(rec: VerificationRecord | None) -> bool:
    if rec is None:
        return False
    diag = dict(getattr(rec, "repair_diagnostics", {}) or {})
    gain = dict(diag.get("post_repair_gain") or {})
    return bool(gain.get("material_gain"))


def _failed_symbolic_check_names(vrec: VerificationRecord | None) -> set[str]:
    checks = ((getattr(vrec, "symbolic_checks", {}) or {}).get("checks") or []) if vrec else []
    names: set[str] = set()
    for item in checks:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip().lower() != "fail":
            continue
        name = str(item.get("name") or "").strip()
        if name:
            names.add(name)
    return names


def _is_catastrophic_rule_incompatibility(vrec: VerificationRecord | None) -> bool:
    if vrec is None:
        return True
    failed_names = _failed_symbolic_check_names(vrec)
    # Only head_vs_goal mismatch is eligible for bounded fallback relaxation.
    if not failed_names:
        return False
    return any(name != "head_vs_goal" for name in failed_names)


def _summarize_backward_plan_candidates(state: ReasoningState | None) -> list[dict[str, Any]]:
    plan = (state.backward_plan or {}) if state else {}
    rows = plan.get("candidates") or []
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "rule_id": row.get("rule_id"),
                "status": row.get("status"),
                "total_score": row.get("total_score"),
                "unification_failure": row.get("unification_failure"),
                "missing_fact_keys_count": len(list(row.get("missing_fact_keys") or [])),
            }
        )
    return out


def _candidate_semantic_guard(
    diag: dict[str, Any],
    *,
    goal: dict[str, Any] | None = None,
    rule: RuleRecord | None = None,
    admission_source: str | None = None,
) -> tuple[bool, str | None, dict[str, Any]]:
    comp = dict(diag.get("score_components") or {})
    sem = float(comp.get("semantic_compatibility", 0.0) or 0.0)
    attractor = float(comp.get("attractor_penalty", 0.0) or 0.0)
    anchor = float(comp.get("semantic_anchor_strength", 0.0) or 0.0)
    logic_form_focus_match = float(comp.get("logic_form_focus_match", 0.0) or 0.0)
    aligned_family = False
    fallback_logic_family_rescue = False
    rescue_meta: dict[str, Any] = {
        "admission_source": str(admission_source or "planner"),
        "semantic_compatibility": sem,
        "attractor_penalty": attractor,
        "semantic_anchor_strength": anchor,
        "logic_form_focus_match": logic_form_focus_match,
    }
    if goal is not None and rule is not None:
        goal_family = _semantic_family((goal or {}).get("predicate"))
        rule_family = _semantic_family(rule.head.predicate if rule.head else "")
        aligned_family = bool(goal_family and rule_family and goal_family == rule_family)
        rule_logic_family = _semantic_family(getattr(rule, "logic_form", ""))
        fallback_logic_family_rescue = bool(
            goal_family
            and rule_logic_family
            and goal_family == rule_logic_family
            and logic_form_focus_match >= 4.0
            and sem > -2.0
        )
        rescue_meta.update(
            {
                "goal_family": goal_family,
                "rule_head_family": rule_family,
                "rule_logic_family": rule_logic_family,
                "aligned_family": aligned_family,
                "fallback_logic_family_rescue": fallback_logic_family_rescue,
            }
        )
    if sem <= -2.0:
        if not aligned_family:
            return False, "semantic_family_mismatch", rescue_meta
    if attractor <= -2.0 and anchor < 2.5:
        if not aligned_family:
            if str(admission_source or "") == "fallback_top_retrieved" and fallback_logic_family_rescue:
                rescue_meta.update(
                    {
                        "fallback_relaxation_applied": True,
                        "rescue_kind": "fallback_logic_form_family_anchor_relaxation",
                    }
                )
                return True, None, rescue_meta
            return False, "attractor_rule_penalized", rescue_meta
    return True, None, rescue_meta


def _collect_goal_rescue_variants(
    goal: dict[str, Any],
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    *,
    max_variants: int = 4,
) -> list[dict[str, Any]]:
    """Build alternative goals by swapping predicate to top retrieved head predicates."""
    base_pred = str((goal or {}).get("predicate") or "").strip()
    goal_args = list((goal or {}).get("args") or [])
    variants: list[dict[str, Any]] = []
    seen: set[str] = {base_pred} if base_pred else set()
    for rule, _score, _meta in ranked:
        head_pred = str(rule.head.predicate if rule.head else "").strip()
        if not head_pred:
            continue
        if head_pred in seen:
            continue
        if str(rule.rule_id).startswith("shared_motif_"):
            continue
        seen.add(head_pred)
        variants.append({"predicate": head_pred, "args": goal_args})
        if len(variants) >= max_variants:
            break
    return variants


def _collect_planner_fallback_rule_ids(
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    *,
    max_rules: int = 3,
) -> list[str]:
    out: list[str] = []
    for rule, _score, _meta in ranked:
        rid = str(rule.rule_id or "").strip()
        if not rid:
            continue
        if rid in out:
            continue
        if rid.startswith("shared_motif_"):
            continue
        out.append(rid)
        if len(out) >= max_rules:
            break
    return out


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
    rescued_fallback_flow: bool = False
    rescued_missing_facts_materiality_hold: bool = False


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


def _has_catastrophic_contradiction(diagnostics: list[str] | None) -> bool:
    """Guardrail: only bypass materiality when no contradiction/conflict signal is present."""
    for item in (diagnostics or []):
        token = str(item or "").lower()
        if "contradiction" in token or "xung_dot" in token or "conflict" in token:
            return True
    return False


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
    question_mode: str = "hybrid",
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

    planner_goal = goal
    plan = build_backward_plan_only(
        goal=goal,
        candidates=ranked,
        known_facts=known_facts,
        reasoning_context=reasoning_context,
        cross_domain_policy=cross_domain_policy,
        structured_facts=structured_facts,
        question_mode=question_mode,
    )
    goal_rescue_attempted = False
    if not plan.candidates and ranked:
        rescue_variants = _collect_goal_rescue_variants(goal, ranked)
        rescue_trace: list[dict[str, Any]] = []
        best_plan = plan
        for alt_goal in rescue_variants:
            goal_rescue_attempted = True
            alt_plan = build_backward_plan_only(
                goal=alt_goal,
                candidates=ranked,
                known_facts=known_facts,
                reasoning_context=reasoning_context,
                cross_domain_policy=cross_domain_policy,
                structured_facts=structured_facts,
                question_mode=question_mode,
            )
            rescue_trace.append(
                {
                    "goal_predicate": alt_goal.get("predicate"),
                    "candidate_count": len(alt_plan.candidates),
                }
            )
            if len(alt_plan.candidates) > len(best_plan.candidates):
                best_plan = alt_plan
                planner_goal = alt_goal
            if alt_plan.candidates:
                break
        out.trace.append(
            {
                "stage": "goal_head_rescue_before_planner",
                "goal_before": goal,
                "goal_after": planner_goal,
                "rescue_attempted": goal_rescue_attempted,
                "rescue_candidates": rescue_trace,
                "plan_candidates_after_rescue": len(best_plan.candidates),
            }
        )
        plan = best_plan

    by_id = {r.rule_id: r for r, _, _ in ranked}
    by_gid = {global_rule_key(r): r for r, _, _ in ranked}
    ranked_diag = {r.rule_id: (d or {}) for r, _s, d in ranked}

    candidate_queue: list[dict[str, Any]] = []
    for cand in plan.candidates:
        candidate_queue.append(
            {
                "rule_id": cand.rule_id,
                "global_rule_key": cand.global_rule_key,
                "admission_source": "planner",
            }
        )

    if not candidate_queue and ranked:
        fallback_ids = _collect_planner_fallback_rule_ids(ranked, max_rules=3)
        for rid in fallback_ids:
            candidate_queue.append(
                {
                    "rule_id": rid,
                    "global_rule_key": None,
                    "admission_source": "fallback_top_retrieved",
                }
            )
        out.trace.append(
            {
                "stage": "planner_admission_fallback",
                "goal": planner_goal,
                "trigger": "admitted_candidates_empty",
                "fallback_rule_ids": fallback_ids,
                "fallback_count": len(fallback_ids),
            }
        )

    # Semantic-first candidate preference for survivor selection.
    if candidate_queue:
        annotated_queue: list[tuple[int, int, dict[str, Any]]] = []
        for idx, item in enumerate(candidate_queue):
            rid = str(item.get("rule_id") or "")
            gkey = item.get("global_rule_key")
            rule = by_gid.get(gkey) if gkey else by_id.get(rid)
            tier, bonus, reason, meta = _semantic_match_tier(goal=planner_goal, rule=rule)
            rank = 2 if tier == "exact" else 1 if tier == "soft" else 0
            item["semantic_family_match_tier"] = tier
            item["semantic_soft_match_bonus"] = bonus
            item["semantic_soft_match_reason"] = reason
            item["semantic_soft_match_meta"] = meta
            annotated_queue.append((rank, idx, item))

        reordered = [it for _rank, _idx, it in sorted(annotated_queue, key=lambda x: (-x[0], x[1]))]
        if [str(x.get("rule_id") or "") for x in reordered] != [str(x.get("rule_id") or "") for x in candidate_queue]:
            out.trace.append(
                {
                    "stage": "candidate_semantic_priority_reorder",
                    "goal": planner_goal,
                    "ordering_policy": "exact_then_soft_then_mismatch",
                    "before": [str(x.get("rule_id") or "") for x in candidate_queue],
                    "after": [str(x.get("rule_id") or "") for x in reordered],
                }
            )
        candidate_queue = reordered

    if not candidate_queue and ranked:
        top_retrieved = [r.rule_id for r, _, _ in ranked[:3]]
        for rid in top_retrieved:
            out.tried_rule_ids.append(rid)
            out.candidate_verdicts[rid] = {
                "rule_id": rid,
                "goal": planner_goal,
                "verification_decision": "REJECT",
                "verification_level": VerificationLevel.HARD_REJECT.value,
                "rejection_reason": ["no_unifiable_candidate_for_goal"],
                "repair_target": "retrieval_or_parse",
                "repair_hints": ["refine_parse_goal", "rerank_with_semantic_constraints"],
                "admission_source": "none",
            }
        out.trace.append(
            {
                "stage": "backward_plan_empty",
                "goal": planner_goal,
                "goal_before_rescue": goal,
                "goal_rescue_attempted": goal_rescue_attempted,
                "decision": "REJECT",
                "reason": "no_unifiable_candidate_for_goal",
                "top_retrieved_rule_ids": top_retrieved,
                "repair_applied": False,
            }
        )
        logger.info(
            "[backward_gate] plan/admission empty for goal=%s (planner_goal=%s); top_retrieved=%s",
            goal.get("predicate"),
            planner_goal.get("predicate") if isinstance(planner_goal, dict) else None,
            top_retrieved,
        )
        out.hard_reject_count = len(top_retrieved)
        out.error = "no_grounded_rule_found"
        return out

    for item in candidate_queue:
        rid = str(item.get("rule_id") or "")
        admission_source = str(item.get("admission_source") or "planner")
        gkey = item.get("global_rule_key")
        rule = by_gid.get(gkey) if gkey else by_id.get(rid)
        if not rule:
            continue
        out.tried_rule_ids.append(rid)

        cand_diag = ranked_diag.get(rid, {})
        semantic_family_match_tier = str(item.get("semantic_family_match_tier") or "mismatch")
        semantic_soft_match_bonus = float(item.get("semantic_soft_match_bonus") or 0.0)
        semantic_soft_match_reason = str(item.get("semantic_soft_match_reason") or "")
        semantic_soft_match_meta = dict(item.get("semantic_soft_match_meta") or {})
        semantic_hard_mismatch_penalty = -2.0 if semantic_family_match_tier == "mismatch" else 0.0
        cand_ok, cand_reason, cand_meta = _candidate_semantic_guard(
            cand_diag,
            goal=planner_goal,
            rule=rule,
            admission_source=admission_source,
        )
        if not cand_ok:
            out.hard_reject_count += 1
            out.candidate_verdicts[rid] = {
                "rule_id": rid,
                "goal": planner_goal,
                "verification_decision": "REJECT",
                "verification_level": VerificationLevel.HARD_REJECT.value,
                "rejection_reason": [cand_reason or "semantic_guard_reject"],
                "repair_target": "retrieval_or_parse",
                "repair_hints": ["rerank_with_semantic_constraints", "avoid_attractor_rule"],
                "admission_source": admission_source,
                "semantic_guard_meta": cand_meta,
                "semantic_soft_match_bonus": semantic_soft_match_bonus,
                "semantic_family_match_tier": semantic_family_match_tier,
                "semantic_hard_mismatch_penalty": semantic_hard_mismatch_penalty,
            }
            out.trace.append(
                {
                    "stage": "candidate_semantic_guard",
                    "rule_id": rid,
                    "admission_source": admission_source,
                    "decision": "REJECT",
                    "reason": cand_reason,
                    "score_components": cand_diag.get("score_components") or {},
                    "guard_meta": cand_meta,
                    "semantic_soft_match_bonus": semantic_soft_match_bonus,
                    "semantic_family_match_tier": semantic_family_match_tier,
                    "semantic_hard_mismatch_penalty": semantic_hard_mismatch_penalty,
                }
            )
            continue

        if cand_meta.get("fallback_relaxation_applied"):
            out.trace.append(
                {
                    "stage": "candidate_semantic_guard_fallback_rescue",
                    "rule_id": rid,
                    "goal": planner_goal,
                    "admission_source": admission_source,
                    "decision": "RELAX_TO_CONTINUE",
                    "rescue_kind": cand_meta.get("rescue_kind"),
                    "guard_meta": cand_meta,
                    "score_components": cand_diag.get("score_components") or {},
                }
            )

        law_span = str((rule.source_ref_full or rule.source_ref) or "")

        rule, v_rule, rtrace = run_rule_repair_loop(
            engine,
            layer2_goal=planner_goal,
            rule_candidate=rule,
            law_span=law_span,
            legal_frame=layer2.query_rule_candidate or "",
            rule_index=rule_index,
            max_attempts=max_rule_repair,
        )

        original_rule_decision = v_rule.final_decision
        original_rule_reasons = list(v_rule.diagnostics)
        has_head_goal_mismatch = any(
            "head_vs_goal" in str(reason or "") or "predicate_mismatch" in str(reason or "")
            for reason in original_rule_reasons
        )
        has_nli_contradiction_high = any(
            str(reason or "").strip() == "nli_contradiction_high"
            for reason in original_rule_reasons
        )
        fallback_rule_relaxation_triggered = False
        fallback_rule_relaxation_reason = ""
        family_soft_match_triggered = False
        family_soft_match_reason = ""
        family_soft_match_meta: dict[str, Any] = {}
        catastrophic_rule_incompatibility = _is_catastrophic_rule_incompatibility(v_rule)
        if has_head_goal_mismatch:
            family_soft_match_triggered, family_soft_match_reason, family_soft_match_meta = _semantic_soft_match_info(
                goal=planner_goal,
                rule=rule,
            )

        if (
            admission_source == "fallback_top_retrieved"
            and bool(cand_meta.get("fallback_relaxation_applied"))
            and original_rule_decision == "REJECT"
            and bool(cand_meta.get("fallback_logic_family_rescue"))
            and (has_head_goal_mismatch or has_nli_contradiction_high)
            and not catastrophic_rule_incompatibility
        ):
            fallback_rule_relaxation_triggered = True
            fallback_rule_relaxation_reason = "rescued_fallback_bounded_rule_verification_relaxation"

        # For fact_application/hybrid mode, relax rule verification for semantically related rules
        fact_application_relaxation_triggered = False
        fact_application_relaxation_reason = ""
        if (
            question_mode in ("fact_application", "hybrid")
            and original_rule_decision == "REJECT"
            and (has_head_goal_mismatch or has_nli_contradiction_high)
            and not catastrophic_rule_incompatibility
            and family_soft_match_triggered
        ):
            fact_application_relaxation_triggered = True
            fact_application_relaxation_reason = "fact_application_or_hybrid_semantic_rule_relaxation"

        effective_rule_decision = (
            "REPAIR" if fallback_rule_relaxation_triggered or fact_application_relaxation_triggered
            else original_rule_decision
        )
        out.trace.append(
            {
                "stage": "rule_gate",
                "rule_id": rid,
                "goal": planner_goal,
                "admission_source": admission_source,
                "final_decision": effective_rule_decision,
                "verification_level": (
                    VerificationLevel.ACCEPT.value if effective_rule_decision == "ACCEPT" else
                    VerificationLevel.SOFT_REJECT.value if effective_rule_decision == "REPAIR" else
                    VerificationLevel.HARD_REJECT.value
                ),
                "rejection_reason": list(v_rule.diagnostics),
                "fallback_rule_verification_relaxation_triggered": fallback_rule_relaxation_triggered,
                "fallback_rule_verification_relaxation_reason": fallback_rule_relaxation_reason,
                "fact_application_rule_relaxation_triggered": fact_application_relaxation_triggered,
                "fact_application_rule_relaxation_reason": fact_application_relaxation_reason,
                "semantic_family_soft_match_triggered": family_soft_match_triggered,
                "semantic_family_soft_match_reason": family_soft_match_reason,
                "semantic_family_soft_match_meta": family_soft_match_meta,
                "semantic_soft_match_bonus": semantic_soft_match_bonus,
                "semantic_family_match_tier": semantic_family_match_tier,
                "semantic_hard_mismatch_penalty": semantic_hard_mismatch_penalty,
                "original_reject_reason": original_rule_reasons,
                "original_final_decision": original_rule_decision,
                "relaxed_final_decision": effective_rule_decision,
                "repair_target": v_rule.repair_target,
                "repair_hints": list(getattr(v_rule, "repair_hints", []) or ([v_rule.repair_hint] if v_rule.repair_hint else [])),
                "repair_applied": getattr(v_rule, "repair_applied", False),
                "rerun_stage": getattr(v_rule, "rerun_stage", None),
                "repair_history": rtrace,
            }
        )

        if fallback_rule_relaxation_triggered:
            out.trace.append(
                {
                    "stage": "rule_gate_fallback_relaxation",
                    "rule_id": rid,
                    "goal": planner_goal,
                    "admission_source": admission_source,
                    "triggered": True,
                    "original_final_decision": original_rule_decision,
                    "original_reject_reason": original_rule_reasons,
                    "relaxed_final_decision": effective_rule_decision,
                    "semantic_guard_meta": cand_meta,
                    "semantic_family_soft_match_triggered": family_soft_match_triggered,
                    "semantic_family_soft_match_reason": family_soft_match_reason,
                    "semantic_family_soft_match_meta": family_soft_match_meta,
                    "catastrophic_rule_incompatibility": catastrophic_rule_incompatibility,
                }
            )

        level = (
            VerificationLevel.ACCEPT
            if effective_rule_decision == "ACCEPT"
            else VerificationLevel.SOFT_REJECT
            if effective_rule_decision == "REPAIR"
            else VerificationLevel.HARD_REJECT
        )
        out.candidate_verdicts[rid] = {
            "rule_id": rid,
            "goal": planner_goal,
            "verification_decision": effective_rule_decision,
            "verification_level": level.value,
            "rejection_reason": list(v_rule.diagnostics),
            "fallback_rule_verification_relaxation_triggered": fallback_rule_relaxation_triggered,
            "semantic_family_soft_match_triggered": family_soft_match_triggered,
            "semantic_family_soft_match_reason": family_soft_match_reason,
            "semantic_family_soft_match_meta": family_soft_match_meta,
            "fact_application_rule_relaxation_triggered": fact_application_relaxation_triggered,
            "semantic_soft_match_bonus": semantic_soft_match_bonus,
            "semantic_family_match_tier": semantic_family_match_tier,
            "semantic_hard_mismatch_penalty": semantic_hard_mismatch_penalty,
            "original_reject_reason": original_rule_reasons,
            "original_final_decision": original_rule_decision,
            "relaxed_final_decision": effective_rule_decision,
            "repair_target": v_rule.repair_target,
            "repair_hints": list(getattr(v_rule, "repair_hints", []) or ([v_rule.repair_hint] if v_rule.repair_hint else [])),
            "admission_source": admission_source,
        }
        logger.info(
            "[rule_gate] candidate rule_id=%s goal=%s decision=%s level=%s reasons=%s",
            rid,
            planner_goal.get("predicate"),
            effective_rule_decision,
            level.value,
            "; ".join(v_rule.diagnostics[:3]),
        )

        if level == VerificationLevel.HARD_REJECT:
            out.hard_reject_count += 1
            continue
        if level == VerificationLevel.SOFT_REJECT:
            out.soft_reject_count += 1

        out.trace.append(
            {
                "stage": "post_rule_gate_survivor",
                "rule_id": rid,
                "goal": planner_goal,
                "admission_source": admission_source,
                "rule_gate_decision": effective_rule_decision,
                "rule_gate_level": level.value,
                "fallback_rule_verification_relaxation_triggered": fallback_rule_relaxation_triggered,
                "semantic_soft_match_bonus": semantic_soft_match_bonus,
                "semantic_family_match_tier": semantic_family_match_tier,
                "semantic_hard_mismatch_penalty": semantic_hard_mismatch_penalty,
            }
        )

        # ← TEMPORAL RE-CHECK BEFORE APPLY
        if reasoning_context and reasoning_context.question_time:
            ok, reason = rule_temporally_valid(rule, reasoning_context.question_time)
            if not ok:
                out.trace.append({
                    "stage": "temporal_recheck_before_apply",
                    "rule_id": rid,
                    "goal": planner_goal,
                    "verification_level": VerificationLevel.HARD_REJECT.value,
                    "rejected": True,
                    "reason": reason,
                })
                out.hard_reject_count += 1
                continue

        selected, bstate = run_backward(
            goal=planner_goal,
            candidates=ranked,
            known_facts=known_facts,
            preferred_rule_id=rid,
            admission_source=admission_source,
            semantic_guard_fallback_rescued=(admission_source == "fallback_top_retrieved"),
            rule_gate_fallback_relaxed=fallback_rule_relaxation_triggered,
            reasoning_context=reasoning_context,
            cross_domain_policy=cross_domain_policy,
            structured_facts=structured_facts,
        )
        backward_plan_rescue = dict((bstate.evaluation_hooks or {}).get("backward_plan_rescue") or {}) if bstate else {}
        out.trace.append(
            {
                "stage": "backward_select_entry",
                "rule_id": rid,
                "goal": planner_goal,
                "admission_source": admission_source,
                "preferred_rule_id": rid,
                "backward_plan_candidates_count": len(_summarize_backward_plan_candidates(bstate)),
                "backward_plan_candidates": _summarize_backward_plan_candidates(bstate),
                "backward_failure_trace": list((bstate.evaluation_hooks or {}).get("failure_trace") or []) if bstate else [],
                "backward_plan_rescue_triggered": bool(backward_plan_rescue.get("triggered")),
                "backward_plan_original_candidate_count": backward_plan_rescue.get("original_candidate_count"),
                "backward_plan_rescued_candidate_count": backward_plan_rescue.get("rescued_candidate_count"),
                "backward_plan_rescue_admission_reason": backward_plan_rescue.get("admission_reason"),
                "backward_plan_final_selected_rule_id": backward_plan_rescue.get("final_selected_rule_id"),
            }
        )
        if not selected:
            out.trace.append(
                {
                    "stage": "backward_select",
                    "rule_id": rid,
                    "goal": planner_goal,
                    "admission_source": admission_source,
                    "verification_level": VerificationLevel.HARD_REJECT.value,
                    "rejected": True,
                    "reason": "backward_reasoner_returned_no_selected_rule",
                    "backward_state_trace": list(bstate.trace or []) if bstate else [],
                    "backward_plan_candidates_count": len(_summarize_backward_plan_candidates(bstate)),
                    "backward_plan_candidates": _summarize_backward_plan_candidates(bstate),
                    "backward_failure_trace": list((bstate.evaluation_hooks or {}).get("failure_trace") or []) if bstate else [],
                    "backward_plan_rescue_triggered": bool(backward_plan_rescue.get("triggered")),
                    "backward_plan_original_candidate_count": backward_plan_rescue.get("original_candidate_count"),
                    "backward_plan_rescued_candidate_count": backward_plan_rescue.get("rescued_candidate_count"),
                    "backward_plan_rescue_admission_reason": backward_plan_rescue.get("admission_reason"),
                    "backward_plan_final_selected_rule_id": backward_plan_rescue.get("final_selected_rule_id"),
                }
            )
            out.hard_reject_count += 1
            continue

        sel, st, v_back, btrace = run_backward_repair_loop(
            engine,
            goal=planner_goal,
            selected_rule=selected,
            bstate=bstate,
            ranked=ranked,
            known_facts=known_facts,
            max_attempts=max_backward_repair,
        )
        rescued_backward_plan_triggered = bool(backward_plan_rescue.get("triggered"))
        rescued_flow_active = bool(
            admission_source == "fallback_top_retrieved"
            and fallback_rule_relaxation_triggered
            and rescued_backward_plan_triggered
        )

        original_back_decision = v_back.final_decision
        original_back_reasons = list(v_back.diagnostics)
        backward_rescue_relaxation_triggered = False
        if rescued_flow_active and original_back_decision == "REJECT":
            reasons = set(str(x or "").strip() for x in original_back_reasons)
            if (
                "fusion_policy_backward_semantic_guard_reject" in reasons
                or "backward_semantic_family_mismatch" in reasons
                or any("semantic_family_alignment:" in x for x in reasons)
            ):
                backward_rescue_relaxation_triggered = True

        effective_back_decision = "REPAIR" if backward_rescue_relaxation_triggered else original_back_decision
        out.trace.append(
            {
                "stage": "backward_gate",
                "initial_rule_id": rid,
                "final_rule_id": sel.rule_id if sel else None,
                "goal": planner_goal,
                "admission_source": admission_source,
                "final_decision": effective_back_decision,
                "verification_level": (
                    VerificationLevel.ACCEPT.value if effective_back_decision == "ACCEPT" else
                    VerificationLevel.SOFT_REJECT.value if effective_back_decision == "REPAIR" else
                    VerificationLevel.HARD_REJECT.value
                ),
                "rejection_reason": list(v_back.diagnostics),
                "backward_rescue_relaxation_triggered": backward_rescue_relaxation_triggered,
                "backward_rescue_relaxation_reason": (
                    "rescued_fallback_backward_semantic_guard_relaxation"
                    if backward_rescue_relaxation_triggered
                    else ""
                ),
                "original_final_decision": original_back_decision,
                "original_reject_reason": original_back_reasons,
                "relaxed_final_decision": effective_back_decision,
                "repair_target": v_back.repair_target,
                "repair_hints": list(getattr(v_back, "repair_hints", []) or ([v_back.repair_hint] if v_back.repair_hint else [])),
                "repair_applied": getattr(v_back, "repair_applied", False),
                "rerun_stage": getattr(v_back, "rerun_stage", None),
                "repair_history": btrace,
            }
        )
        if backward_rescue_relaxation_triggered:
            out.trace.append(
                {
                    "stage": "backward_gate_rescued_relaxation",
                    "rule_id": sel.rule_id if sel else rid,
                    "admission_source": admission_source,
                    "triggered": True,
                    "original_final_decision": original_back_decision,
                    "original_reject_reason": original_back_reasons,
                    "relaxed_final_decision": effective_back_decision,
                }
            )
        logger.info(
            "[backward_gate] candidate rule_id=%s final_rule_id=%s goal=%s decision=%s reasons=%s",
            rid,
            sel.rule_id if sel else None,
            planner_goal.get("predicate"),
            effective_back_decision,
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
                        "goal": planner_goal,
                        "verification_level": VerificationLevel.HARD_REJECT.value,
                        "rejected": True,
                        "reason": reason,
                    })
                    out.hard_reject_count += 1
                    continue
            
            law2 = str((sel.source_ref_full or sel.source_ref) or "")
            _, v_rule2, rtrace2 = run_rule_repair_loop(
                engine,
                layer2_goal=planner_goal,
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
            backward_ok_for_clarify = v_back.final_decision in ("ACCEPT", "REPAIR") and (
                v_back.final_decision == "ACCEPT" or _repair_material_gain(v_back)
            )
            # For fact_application mode, allow missing facts to proceed to conditional reasoning
            if question_mode in ("fact_application", "hybrid") and not backward_ok_for_clarify:
                rescued_materiality_keepalive = bool(
                    rescued_flow_active
                    and effective_back_decision in ("ACCEPT", "REPAIR")
                    and not _has_catastrophic_contradiction(v_back.diagnostics)
                )
                if rescued_materiality_keepalive or question_mode == "fact_application":
                    out.trace.append(
                        {
                            "stage": "backward_materiality_guard_rescued_keepalive",
                            "rule_id": sel.rule_id if sel else rid,
                            "decision": "KEEP_FOR_CONDITIONAL_REASONING",
                            "reason": "fact_application_mode_missing_facts_allowed" if question_mode == "fact_application" else "rescued_fallback_missing_facts_without_catastrophic_contradiction",
                            "missing_facts": list(st.missing_facts or []),
                            "repair_diagnostics": getattr(v_back, "repair_diagnostics", {}),
                        }
                    )
                    out.ok = True
                    out.clarification_needed = False  # Don't require clarification for fact_application
                    out.selected = sel
                    out.bstate = st
                    out.v_rule = v_rule
                    out.v_back = v_back
                    out.rescued_fallback_flow = True
                    out.rescued_missing_facts_materiality_hold = True
                    return out
            if not backward_ok_for_clarify:
                rescued_materiality_keepalive = bool(
                    rescued_flow_active
                    and effective_back_decision in ("ACCEPT", "REPAIR")
                    and not _has_catastrophic_contradiction(v_back.diagnostics)
                )
                if rescued_materiality_keepalive:
                    out.trace.append(
                        {
                            "stage": "backward_materiality_guard_rescued_keepalive",
                            "rule_id": sel.rule_id if sel else rid,
                            "decision": "KEEP_FOR_CONDITIONAL_REASONING",
                            "reason": "rescued_fallback_missing_facts_without_catastrophic_contradiction",
                            "missing_facts": list(st.missing_facts or []),
                            "repair_diagnostics": getattr(v_back, "repair_diagnostics", {}),
                        }
                    )
                    out.ok = True
                    out.clarification_needed = True
                    out.selected = sel
                    out.bstate = st
                    out.v_rule = v_rule
                    out.v_back = v_back
                    out.rescued_fallback_flow = True
                    out.rescued_missing_facts_materiality_hold = True
                    return out
                out.hard_reject_count += 1
                out.trace.append(
                    {
                        "stage": "backward_materiality_guard",
                        "rule_id": sel.rule_id if sel else rid,
                        "decision": "REJECT",
                        "reason": "backward_repair_without_material_gain",
                        "repair_diagnostics": getattr(v_back, "repair_diagnostics", {}),
                    }
                )
                continue
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
            out.clarification_needed = bool(critical_missing) and question_mode not in ("fact_application", "hybrid")  # Don't require clarification for fact_application
            out.selected = sel
            out.bstate = st
            out.v_rule = v_rule
            out.v_back = v_back
            return out

        if effective_back_decision == "ACCEPT" and sel:
            out.ok = True
            out.clarification_needed = False
            out.selected = sel
            out.bstate = st
            out.v_rule = v_rule
            out.v_back = v_back
            out.rescued_fallback_flow = rescued_flow_active
            return out

        if effective_back_decision == "REPAIR" and sel:
            out.soft_reject_count += 1
            if _repair_material_gain(v_back) or backward_rescue_relaxation_triggered:
                out.ok = True
                out.clarification_needed = False
                out.selected = sel
                out.bstate = st
                out.v_rule = v_rule
                out.v_back = v_back
                out.rescued_fallback_flow = rescued_flow_active
                out.trace.append(
                    {
                        "stage": "backward_repair_promoted_for_rescued_fallback",
                        "rule_id": sel.rule_id,
                        "decision": "PROMOTE_TO_FORWARD",
                        "reason": (
                            "rescued_fallback_backward_verification_relaxed"
                            if backward_rescue_relaxation_triggered
                            else "backward_repair_with_material_gain"
                        ),
                    }
                )
                return out
            out.trace.append(
                {
                    "stage": "backward_repair_not_promoted",
                    "rule_id": sel.rule_id,
                    "decision": "REJECT",
                    "reason": "backward_requires_accept_for_final_promotion",
                }
            )

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
    rescued_fallback_flow: bool = False,
    semantic_match_context: dict[str, Any] | None = None,
    question_mode: str = "hybrid",
) -> ForwardGateOutcome:
    """Run forward + proof, then ``verify_forward`` with optional repair (re-run forward + rebuild proof)."""
    out = ForwardGateOutcome(ok=False)
    sf = dict(session.structured_facts) if session.structured_facts else None
    sem_ctx = dict(semantic_match_context or {})
    semantic_family_match_tier = str(sem_ctx.get("semantic_family_match_tier") or "mismatch")
    semantic_soft_match_triggered = bool(sem_ctx.get("semantic_soft_match_triggered"))
    semantic_soft_match_reason = str(sem_ctx.get("semantic_soft_match_reason") or "")
    out.trace.append(
        {
            "stage": "forward_semantic_context",
            "semantic_family_match_tier": semantic_family_match_tier,
            "semantic_soft_match_triggered": semantic_soft_match_triggered,
            "semantic_soft_match_reason": semantic_soft_match_reason,
            "forward_soft_match_relaxation_triggered": False,
            "forward_soft_match_relaxation_reason": "",
        }
    )

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
            question_mode=question_mode,
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

    fail_reason = (fst.forward_result or {}).get("failure_reason") if fst and fst.forward_result else None
    if (
        v_fwd.final_decision == "REJECT"
        and str(fail_reason or "") == "predicate_family_mismatch"
        and semantic_family_match_tier == "soft"
    ):
        out.trace.append(
            {
                "stage": "forward_soft_match_relaxation",
                "semantic_family_match_tier": semantic_family_match_tier,
                "forward_soft_match_relaxation_triggered": False,
                "forward_soft_match_relaxation_reason": "predicate_family_mismatch_soft_semantic_compatibility_rejected",
                "failure_reason": fail_reason,
                "decision": "retain_reject",
                "partial_forward_soft_match": False,
            }
        )

    if rescued_fallback_flow and v_fwd.final_decision == "REJECT":
        out.trace.append(
            {
                "stage": "forward_gate_rescued_relaxation",
                "triggered": True,
                "original_final_decision": "REJECT",
                "original_reject_reason": list(v_fwd.diagnostics),
                "relaxed_final_decision": "REPAIR",
                "reason": "rescued_fallback_forward_verification_relaxation",
            }
        )
        out.ok = True
        return out

    # For fact_application/hybrid mode, allow incomplete forward proofs to proceed
    # as conditional reasoning (A+B) when failure is due to absent facts.
    if question_mode in ("fact_application", "hybrid") and v_fwd.final_decision == "REJECT":
        fail_reason = (fst.forward_result or {}).get("failure_reason") if fst and fst.forward_result else None
        missing_facts_now = list(getattr(fst, "missing_facts", None) or []) if fst else []
        fail_key = str(fail_reason or "").strip().lower()
        conditional_failures = {
            "unification_broken",
            "missing_input",
            "constraint_missing_input",
            "positive_condition_missing",
        }
        unification_from_absent_facts = fail_key in {"unification_broken", "actor_role_mismatch"} and bool(missing_facts_now)
        if fail_key in conditional_failures or unification_from_absent_facts:
            out.trace.append(
                {
                    "stage": "forward_gate_conditional_relaxation",
                    "triggered": True,
                    "original_final_decision": "REJECT",
                    "original_reject_reason": list(v_fwd.diagnostics),
                    "relaxed_final_decision": "CONDITIONAL",
                    "reason": "fact_application_mode_incomplete_proof_allowed",
                    "failure_reason": fail_reason,
                    "missing_facts": missing_facts_now,
                }
            )
            out.ok = True
            return out

    fail_rule = selected
    if fst and fst.forward_result and fst.forward_result.get("rule_id"):
        by_id = {r.rule_id: r for r, _, _ in ranked}
        fail_rule = by_id.get(str(fst.forward_result.get("rule_id")), selected)
    quality_failures = {
        "unknown_goal_atom",
        "unknown_rule_head",
        "predicate_family_mismatch",
        "actor_role_mismatch",
        "constraint_schema_missing",
        "noncanonical_goal_surface",
        "weak_shared_template",
        "unification_broken",
    }
    fallback_conclusion = conc
    if not fallback_conclusion:
        if str(fail_reason or "") in quality_failures:
            fallback_conclusion = f"Forward blocked by runtime quality gate ({fail_reason})."
        else:
            fallback_conclusion = f"Kết luận tạm thời theo quy tắc {fail_rule.rule_id}: cần làm rõ thêm điều kiện."
    out.proof_obj = build_partial_proof(
        rule=fail_rule,
        used_facts=list(known_facts.keys()),
        conclusion=fallback_conclusion,
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
