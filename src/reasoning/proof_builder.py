"""Assemble proof objects for the QA pipeline."""

from __future__ import annotations

from typing import Any

from schemas.proof import ProofObject, ProofStep
from schemas.rule import RuleRecord
from utils.ids import new_proof_id


def build_proof(
    *,
    rule: RuleRecord,
    used_facts: list[str],
    conclusion: str,
) -> ProofObject:
    steps: list[ProofStep] = [
        ProofStep(step_id=1, description=f"Matched curated rule {rule.rule_id}", rule_id=rule.rule_id),
        ProofStep(step_id=2, description="Verified user / session facts for rule requirements", fact_keys=used_facts),
        ProofStep(step_id=3, description=f"Derived conclusion: {conclusion}", rule_id=rule.rule_id),
    ]
    prov = {
        "source_ref": rule.source_ref,
        "source_ref_full": rule.source_ref_full,
        "logic_form": rule.logic_form,
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
