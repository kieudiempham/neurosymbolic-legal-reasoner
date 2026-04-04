"""Lightweight proof validity hooks for future evaluation pipelines."""

from __future__ import annotations

from typing import Any

from reasoning.semantics.plan_models import ProofStepRecord


def validate_proof_step(step: ProofStepRecord | dict[str, Any]) -> tuple[bool, list[str]]:
    s = step if isinstance(step, ProofStepRecord) else ProofStepRecord.model_validate(step)
    issues: list[str] = []
    if s.status == "ok" and not s.derived_atom:
        issues.append("missing_derived_atom")
    if s.status == "ok" and not s.rule_id:
        issues.append("missing_rule_id")
    return (len(issues) == 0, issues)


def validate_proof_chain(steps: list[Any]) -> tuple[bool, list[str]]:
    all_issues: list[str] = []
    for i, st in enumerate(steps):
        ok, iss = validate_proof_step(st)
        if not ok:
            all_issues.extend([f"step{i}:{x}" for x in iss])
    return (len(all_issues) == 0, all_issues)
