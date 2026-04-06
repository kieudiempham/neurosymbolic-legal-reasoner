"""Structured reasoning outcome for domain-aware runtime (phase 2–3)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReasoningResult(BaseModel):
    """First-class artifact: retrieval + bridge + conflict/temporal + proof-oriented summary."""

    active_domains_used: list[str] = Field(default_factory=list)
    bridge_rules_used: list[str] = Field(default_factory=list)
    bridge_generated_facts: list[dict[str, Any]] = Field(default_factory=list)
    candidate_rules_considered: list[str] = Field(default_factory=list)
    rejected_candidates_domain_policy: list[dict[str, Any]] = Field(default_factory=list)
    rejected_candidates_temporal: list[dict[str, Any]] = Field(default_factory=list)
    rejected_candidates_conflict: list[dict[str, Any]] = Field(default_factory=list)
    rejected_candidates: list[dict[str, Any]] = Field(default_factory=list)
    subgoals_satisfied: list[str] = Field(default_factory=list)
    subgoals_unresolved: list[str] = Field(default_factory=list)
    unresolved_subgoals_domain: list[str] = Field(default_factory=list)
    proof_summary_by_domain: dict[str, list[str]] = Field(default_factory=dict)
    cross_domain_jumps_logged: list[dict[str, Any]] = Field(default_factory=list)
    policy_snapshot: dict[str, Any] = Field(default_factory=dict)
    reasoning_confidence: float | None = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    final_winning_rule_ids: list[str] = Field(default_factory=list)
    rule_id_collision_warnings: list[dict[str, Any]] = Field(default_factory=list)
    namespacing_mode: str = "global_rule_key_v1"
    domain_rejected_candidates_logic_layer: list[dict[str, Any]] = Field(default_factory=list)
    bridge_facts_consumed: list[str] = Field(default_factory=list)
    logic_layer_policy_decisions: list[dict[str, Any]] = Field(default_factory=list)
    cross_domain_jumps_attempted: int = 0
    cross_domain_jumps_blocked: int = 0
    winning_rule_reason: str | None = None
    override_applied: bool = False
    exception_applied: bool = False
    shared_layer_rules_used: list[str] = Field(default_factory=list)
    shared_bridge_facts_generated: list[str] = Field(default_factory=list)
    cross_layer_reasoning_steps: list[dict[str, Any]] = Field(default_factory=list)
