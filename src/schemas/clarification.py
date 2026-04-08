"""Clarification artifact schema for two-step clarification protocol."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ClarificationTarget(BaseModel):
    fact_key: str
    target_kind: str = ""
    expected_type: str = ""


class ClarificationArtifact(BaseModel):
    needs_clarification: bool = False
    clarification_targets: list[ClarificationTarget] = Field(default_factory=list)
    clarification_question: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)
