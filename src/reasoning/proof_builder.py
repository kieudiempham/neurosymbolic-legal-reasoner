"""Assemble proof objects for the QA pipeline."""

from __future__ import annotations

import json
from typing import Any

from schemas.proof import ProofObject, ProofStep
from schemas.rule import RuleRecord
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.internal.models import ReasoningRule
from utils.ids import new_proof_id


def build_proof(
    *,
    rule: RuleRecord,
    used_facts: list[str],
    conclusion: str,
    forward_result: dict[str, Any] | None = None,
) -> ProofObject:
    rr = map_rule_record_to_reasoning_rule(rule)
    return build_proof_with_reasoning(
        rule=rule,
        reasoning_rule=rr,
        used_facts=used_facts,
        conclusion=conclusion,
        forward_result=forward_result,
    )


def build_proof_with_reasoning(
    *,
    rule: RuleRecord,
    reasoning_rule: ReasoningRule,
    used_facts: list[str],
    conclusion: str,
    forward_result: dict[str, Any] | None = None,
) -> ProofObject:
    """Proof với goal_atom, supporting atoms, optional forward semantic trace."""
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
    steps: list[ProofStep] = [
        ProofStep(
            step_id=1,
            description=f"Khớp luật {rule.rule_id} (logic_form={reasoning_rule.logic_form})",
            rule_id=rule.rule_id,
        ),
        ProofStep(
            step_id=2,
            description=f"Mục tiêu suy luận (goal_atom): {atom_summary}",
            rule_id=rule.rule_id,
        ),
        ProofStep(
            step_id=3,
            description="Đã xét điều kiện dương / phủ định / ngoại lệ / ràng buộc theo schema nội bộ",
            fact_keys=used_facts,
        ),
    ]
    if forward_result and forward_result.get("proof_steps"):
        for i, ps in enumerate(forward_result["proof_steps"]):
            steps.append(
                ProofStep(
                    step_id=10 + i,
                    description="Bước suy diễn tiến (forward semantics)",
                    rule_id=ps.get("rule_id") or rule.rule_id,
                    fact_keys=used_facts,
                    derived_atom=ps.get("derived_atom"),
                    supporting_atoms=ps.get("supporting_atoms"),
                    substitution=ps.get("substitution"),
                    applied_constraints=ps.get("applied_constraints"),
                    status=ps.get("status"),
                    failure_reason=ps.get("failure_reason"),
                )
            )

    steps.append(
        ProofStep(step_id=4, description=f"Kết luận hình thức: {conclusion}", rule_id=rule.rule_id)
    )
    prov = {
        "source_ref": rule.source_ref,
        "source_ref_full": rule.source_ref_full,
        "logic_form": rule.logic_form,
        "goal_atom": list(reasoning_rule.goal_atom),
        "applied_constraint_types": [type(c).__name__ for c in reasoning_rule.constraints],
        "forward_substitution": (forward_result or {}).get("substitution"),
        "constraint_traces": (forward_result or {}).get("constraint_traces"),
    }
    return ProofObject(
        proof_id=new_proof_id(),
        used_facts=used_facts,
        used_rules=[rule.rule_id],
        derived_conclusion=conclusion,
        proof_steps=steps,
        provenance=prov,
    )


class ProofBuilder:
    """Legacy stub — use build_proof() for the QA pipeline."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def build(self, reasoning_bundle: dict[str, Any]) -> Any:
        raise NotImplementedError
