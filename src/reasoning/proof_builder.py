"""Assemble proof objects for the QA pipeline."""

from __future__ import annotations

import json
from typing import Any

from schemas.proof import ProofObject, ProofStep
from schemas.rule import RuleRecord
from schemas.rule_metadata import meta_for_proof_and_trace
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.internal.models import ReasoningRule
from runtime.reasoning_context import ReasoningContext
from utils.ids import new_proof_id


def build_proof(
    *,
    rule: RuleRecord,
    used_facts: list[str],
    conclusion: str,
    forward_result: dict[str, Any] | None = None,
    requirement_artifact: dict[str, Any] | None = None,
    reasoning_context: ReasoningContext | None = None,
    candidate_rules: dict[str, RuleRecord] | None = None,
    phase3_context: dict[str, Any] | None = None,
) -> ProofObject:
    rr = map_rule_record_to_reasoning_rule(rule)
    return build_proof_with_reasoning(
        rule=rule,
        reasoning_rule=rr,
        used_facts=used_facts,
        conclusion=conclusion,
        forward_result=forward_result,
        requirement_artifact=requirement_artifact,
        reasoning_context=reasoning_context,
        candidate_rules=candidate_rules,
        phase3_context=phase3_context,
    )


def _meta_step(rule: RuleRecord, candidate_rules: dict[str, RuleRecord] | None, rid: str | None) -> dict[str, Any]:
    r = rule
    if rid and candidate_rules:
        r = candidate_rules.get(rid, rule)
    return meta_for_proof_and_trace(r)


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        key = str(raw or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _premise_sets(
    requirement_artifact: dict[str, Any] | None,
    used_facts: list[str],
) -> tuple[list[str], list[str]]:
    if not requirement_artifact:
        return _dedupe(list(used_facts)), []
    satisfied = _dedupe(list(requirement_artifact.get("satisfied") or []))
    missing = _dedupe(
        list(requirement_artifact.get("unmet_required") or [])
        + list(requirement_artifact.get("unmet_optional") or [])
    )
    return satisfied, missing


def _exception_status_from_forward(forward_result: dict[str, Any] | None) -> str:
    reason = str((forward_result or {}).get("failure_reason") or "").strip().lower()
    if reason in {"exception_triggered", "negative_condition_blocked"}:
        return "triggered"
    if reason in {"exception_unknown", "unless_condition_unknown"}:
        return "unknown"
    return "none"


def _fail_stage(forward_result: dict[str, Any] | None) -> str | None:
    reason = str((forward_result or {}).get("failure_reason") or "").strip().lower()
    if not reason:
        return None
    if "constraint" in reason:
        return "constraint_check"
    if "exception" in reason or "negative" in reason or "unless" in reason:
        return "exception_check"
    if "positive_condition" in reason:
        return "premise_match"
    return "forward_semantics"


def build_partial_proof(
    *,
    rule: RuleRecord,
    used_facts: list[str],
    conclusion: str,
    forward_result: dict[str, Any] | None = None,
    reasoning_context: ReasoningContext | None = None,
    requirement_artifact: dict[str, Any] | None = None,
    candidate_rules: dict[str, RuleRecord] | None = None,
    phase3_context: dict[str, Any] | None = None,
) -> ProofObject:
    failure_reason = str((forward_result or {}).get("failure_reason") or "").strip() or "forward_verification_failed"
    stage = _fail_stage(forward_result) or "forward_semantics"
    satisfied, missing = _premise_sets(requirement_artifact, used_facts)
    m0 = _meta_step(rule, candidate_rules, rule.rule_id)
    step = ProofStep(
        step_id=1,
        description=f"Forward reasoning did not complete at stage={stage}; reason={failure_reason}",
        rule_id=rule.rule_id,
        fact_keys=used_facts,
        status="failed",
        failure_reason=failure_reason,
        conclusion={"kind": "forward_failure", "stage": stage, "reason": failure_reason},
        step_type="forward_failure",
        rulebase_id=m0["rulebase_id"],
        domain=m0["domain"],
        layer=m0["layer"],
        source_doc=m0["source_doc"],
        source_article=m0["source_article"],
    )
    prov = {
        "source_ref": rule.source_ref,
        "source_ref_full": rule.source_ref_full,
        "logic_form": rule.logic_form,
        "forward_substitution": (forward_result or {}).get("substitution"),
        "constraint_traces": (forward_result or {}).get("constraint_traces"),
        "reasoning_context": reasoning_context.to_trace_dict() if reasoning_context else None,
        "rulebase_provenance": m0,
        "phase3": phase3_context,
        "failure_reason": failure_reason,
        "failure_stage": stage,
    }
    return ProofObject(
        proof_id=new_proof_id(),
        selected_rule=rule.rule_id,
        used_facts=used_facts,
        used_rules=[rule.rule_id],
        conclusion=conclusion,
        derived_conclusion=conclusion,
        satisfied_premises=satisfied,
        missing_premises=missing,
        exception_status=_exception_status_from_forward(forward_result),
        fail_stage=stage,
        proof_steps=[step],
        provenance=prov,
    )


def build_proof_with_reasoning(
    *,
    rule: RuleRecord,
    reasoning_rule: ReasoningRule,
    used_facts: list[str],
    conclusion: str,
    forward_result: dict[str, Any] | None = None,
    requirement_artifact: dict[str, Any] | None = None,
    reasoning_context: ReasoningContext | None = None,
    candidate_rules: dict[str, RuleRecord] | None = None,
    phase3_context: dict[str, Any] | None = None,
) -> ProofObject:
    """Proof với goal_atom, supporting atoms, optional forward semantic trace."""
    m0 = _meta_step(rule, candidate_rules, rule.rule_id)
    atom_summary = json.dumps(
        {
            "goal_atom": [reasoning_rule.goal_atom[0], *list(reasoning_rule.goal_atom[1:])],
            "positive_n": len(reasoning_rule.positive_conditions),
            "negative_n": len(reasoning_rule.negative_conditions),
            "exception_n": len(reasoning_rule.exception_conditions),
            "constraints_n": len(reasoning_rule.constraints),
        },
        ensure_ascii=False,
    )
    pol_check = ""
    if reasoning_context and reasoning_context.cross_domain_policy:
        pol_check = str(reasoning_context.cross_domain_policy.to_trace_dict())

    steps: list[ProofStep] = []
    sid = 0
    if phase3_context:
        bf = phase3_context.get("bridge_facts") or []
        gids = [str(x.get("fact_key", "")) for x in bf if isinstance(x, dict)]
        if gids:
            sid += 1
            steps.append(
                ProofStep(
                    step_id=sid,
                    description="Suy luận bridge (shared): sinh fact trung gian phục vụ domain/statute",
                    step_type="bridge_inference",
                    fact_keys=gids,
                    generated_fact_ids=gids,
                    conclusion={"kind": "bridge_facts", "n": len(gids)},
                    temporal_check=phase3_context.get("temporal"),
                )
            )
        tr = phase3_context.get("temporal_rejected_count", 0)
        cr = phase3_context.get("conflict_rejected_count", 0)
        if tr or cr:
            sid += 1
            steps.append(
                ProofStep(
                    step_id=sid,
                    description=f"Lọc policy pha 3: temporal_rejected={tr}, conflict_rejected={cr}",
                    step_type="policy_filter",
                    temporal_check=phase3_context.get("temporal"),
                    conflict_resolution={
                        "temporal_rejected": tr,
                        "conflict_rejected": cr,
                    },
                )
            )

    # Add legal policy steps for Part B
    if phase3_context and phase3_context.get("legal_policy_applied"):
        policy_data = phase3_context["legal_policy_applied"]
        if policy_data.get("temporal_recheck_applied"):
            sid += 1
            steps.append(
                ProofStep(
                    step_id=sid,
                    description="Re-check temporal validity at apply point (Part B)",
                    step_type="temporal_recheck_apply",
                    temporal_check=policy_data.get("temporal_recheck_result"),
                    conclusion={"kind": "temporal_recheck", "passed": policy_data.get("temporal_recheck_passed", True)},
                )
            )
        if policy_data.get("conflict_resolution_applied"):
            sid += 1
            steps.append(
                ProofStep(
                    step_id=sid,
                    description="Conflict resolution at apply point (Part B)",
                    step_type="conflict_resolution_apply",
                    conflict_resolution=policy_data.get("conflict_resolution_result"),
                    conclusion={"kind": "conflict_resolution", "resolved": policy_data.get("conflict_resolved", True)},
                )
            )
        if policy_data.get("override_applied") or policy_data.get("exception_applied"):
            sid += 1
            steps.append(
                ProofStep(
                    step_id=sid,
                    description="Override/exception applied (Part B)",
                    step_type="override_exception_apply",
                    conclusion={
                        "kind": "override_exception",
                        "override_applied": policy_data.get("override_applied", False),
                        "exception_applied": policy_data.get("exception_applied", False),
                    },
                )
            )

    base_id = len(steps)
    n0 = base_id
    steps.extend([
        ProofStep(
            step_id=n0 + 1,
            description=f"Khớp luật {rule.rule_id} (logic_form={reasoning_rule.logic_form})",
            rule_id=rule.rule_id,
            premises=list(reasoning_rule.positive_conditions) if reasoning_rule.positive_conditions else None,
            conclusion={"kind": "rule_match", "rule_id": rule.rule_id},
            rulebase_id=m0["rulebase_id"],
            domain=m0["domain"],
            layer=m0["layer"],
            source_doc=m0["source_doc"],
            source_article=m0["source_article"],
            step_type="domain_rule",
            policy_check=pol_check or None,
        ),
        ProofStep(
            step_id=n0 + 2,
            description=f"Mục tiêu suy luận (goal_atom): {atom_summary}",
            rule_id=rule.rule_id,
            premises=None,
            conclusion={"kind": "goal_atom", "summary": atom_summary},
            rulebase_id=m0["rulebase_id"],
            domain=m0["domain"],
            layer=m0["layer"],
            source_doc=m0["source_doc"],
            source_article=m0["source_article"],
        ),
        ProofStep(
            step_id=n0 + 3,
            description="Đã xét điều kiện dương / phủ định / ngoại lệ / ràng buộc theo schema nội bộ",
            fact_keys=used_facts,
            premises=used_facts,
            conclusion={"kind": "conditions_reviewed"},
            rulebase_id=m0["rulebase_id"],
            domain=m0["domain"],
            layer=m0["layer"],
            source_doc=m0["source_doc"],
            source_article=m0["source_article"],
        ),
    ])
    fwd_list = (forward_result or {}).get("proof_steps") or []
    if forward_result and fwd_list:
        for i, ps in enumerate(fwd_list):
            rid = ps.get("rule_id") or rule.rule_id
            mx = _meta_step(rule, candidate_rules, str(rid) if rid else None)
            steps.append(
                ProofStep(
                    step_id=n0 + 4 + i,
                    description="Bước suy diễn tiến (forward semantics)",
                    rule_id=str(rid) if rid else rule.rule_id,
                    fact_keys=used_facts,
                    derived_atom=ps.get("derived_atom"),
                    supporting_atoms=ps.get("supporting_atoms"),
                    substitution=ps.get("substitution"),
                    applied_constraints=ps.get("applied_constraints"),
                    status=ps.get("status"),
                    failure_reason=ps.get("failure_reason"),
                    premises=ps.get("supporting_atoms"),
                    conclusion={"kind": "forward_step", "derived_atom": ps.get("derived_atom")},
                    rulebase_id=mx["rulebase_id"],
                    domain=mx["domain"],
                    layer=mx["layer"],
                    source_doc=mx["source_doc"],
                    source_article=mx["source_article"],
                )
            )

    steps.append(
        ProofStep(
            step_id=n0 + 4 + len(fwd_list),
            description=f"Kết luận hình thức: {conclusion}",
            rule_id=rule.rule_id,
            conclusion={"kind": "final", "text": conclusion},
            rulebase_id=m0["rulebase_id"],
            domain=m0["domain"],
            layer=m0["layer"],
            source_doc=m0["source_doc"],
            source_article=m0["source_article"],
        )
    )
    prov = {
        "source_ref": rule.source_ref,
        "source_ref_full": rule.source_ref_full,
        "logic_form": rule.logic_form,
        "goal_atom": list(reasoning_rule.goal_atom),
        "applied_constraint_types": [type(c).__name__ for c in reasoning_rule.constraints],
        "forward_substitution": (forward_result or {}).get("substitution"),
        "constraint_traces": (forward_result or {}).get("constraint_traces"),
        "reasoning_context": reasoning_context.to_trace_dict() if reasoning_context else None,
        "rulebase_provenance": m0,
        "phase3": phase3_context,
    }
    satisfied, missing = _premise_sets(requirement_artifact, used_facts)
    return ProofObject(
        proof_id=new_proof_id(),
        selected_rule=rule.rule_id,
        used_facts=used_facts,
        used_rules=[rule.rule_id],
        conclusion=conclusion,
        derived_conclusion=conclusion,
        satisfied_premises=satisfied,
        missing_premises=missing,
        exception_status=_exception_status_from_forward(forward_result),
        fail_stage=_fail_stage(forward_result),
        proof_steps=steps,
        provenance=prov,
    )


class ProofBuilder:
    """Legacy stub — use build_proof() for the QA pipeline."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def build(self, reasoning_bundle: dict[str, Any]) -> Any:
        raise NotImplementedError
