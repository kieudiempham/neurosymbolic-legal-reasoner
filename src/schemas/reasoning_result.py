"""Structured reasoning outcome for domain-aware runtime (phase 2)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReasoningResult(BaseModel):
    """Augments session/trace — produced alongside proof in domain-aware runs."""

    active_domains_used: list[str] = Field(default_factory=list)
    bridge_rules_used: list[str] = Field(default_factory=list)
    rejected_candidates: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_subgoals_domain: list[str] = Field(default_factory=list)
    proof_summary_by_domain: dict[str, list[str]] = Field(default_factory=dict)
    cross_domain_jumps_logged: list[dict[str, Any]] = Field(default_factory=list)
    policy_snapshot: dict[str, Any] = Field(default_factory=dict)
