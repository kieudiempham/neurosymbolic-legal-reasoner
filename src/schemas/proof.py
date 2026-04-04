"""Proof object for explainability (QA pipeline)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProofStep(BaseModel):
    step_id: int
    description: str
    rule_id: str | None = None
    fact_keys: list[str] = Field(default_factory=list)
    derived_atom: list[Any] | None = None
    supporting_atoms: list[list[Any]] | None = None
    substitution: dict[str, Any] | None = None
    applied_constraints: list[dict[str, Any]] | None = None
    status: str | None = None
    failure_reason: str | None = None


class ProofObject(BaseModel):
    proof_id: str
    used_facts: list[str] = Field(default_factory=list)
    used_rules: list[str] = Field(default_factory=list)
    derived_conclusion: str = ""
    proof_steps: list[ProofStep] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
