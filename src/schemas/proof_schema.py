"""Structured proof objects for backward/forward reasoning traces."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProofStep(BaseModel):
    """One step in a proof (rule application or fact assertion)."""

    step_id: str
    kind: Literal["fact", "rule", "assumption", "unknown"]
    description: str
    antecedent_step_ids: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class Proof(BaseModel):
    """A full proof DAG / list backing explainable answers."""

    proof_id: str
    question_id: str | None = None
    steps: list[ProofStep] = Field(default_factory=list)
    conclusion: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
