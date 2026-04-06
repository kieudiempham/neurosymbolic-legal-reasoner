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
    # Multi-rulebase provenance (optional; phase 1)
    premises: list[Any] | None = None
    conclusion: dict[str, Any] | None = None
    rulebase_id: str | None = None
    domain: str | None = None
    layer: str | None = None
    source_doc: str | None = None
    source_article: str | None = None
    # Phase 2 — domain-aware proof
    step_type: str | None = None
    cross_domain_from: str | None = None
    cross_domain_to: str | None = None
    jump_reason: str | None = None
    policy_check: str | None = None


class ProofObject(BaseModel):
    proof_id: str
    used_facts: list[str] = Field(default_factory=list)
    used_rules: list[str] = Field(default_factory=list)
    derived_conclusion: str = ""
    proof_steps: list[ProofStep] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
