"""Backward / forward reasoning state."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

GoalStatus = Literal["open", "satisfied", "failed", "unknown"]


class RequirementItem(BaseModel):
    """Single requirement from rule body (symbolic string or structured)."""

    key: str
    description: str = ""
    predicate: str | None = None
    args: list[Any] = Field(default_factory=list)
    # Internal reasoning layer (optional; backward compatible when absent)
    requirement_kind: str | None = None
    atom_payload: dict[str, Any] | None = None


class ReasoningState(BaseModel):
    requirement_set: list[RequirementItem] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    selected_rule_ids: list[str] = Field(default_factory=list)
    derived_facts: list[str] = Field(default_factory=list)
    goal_status: GoalStatus = "open"
    covered_requirements: list[str] = Field(default_factory=list)
    can_continue_forward: bool = False
    trace: list[str] = Field(default_factory=list)
    # Runtime semantic layer (optional; backward-compatible when absent)
    backward_plan: dict[str, Any] | None = None
    forward_result: dict[str, Any] | None = None
    failure_reason: str | None = None
    evaluation_hooks: dict[str, Any] | None = None
