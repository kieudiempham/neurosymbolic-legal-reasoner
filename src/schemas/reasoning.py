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


class ReasoningState(BaseModel):
    requirement_set: list[RequirementItem] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    selected_rule_ids: list[str] = Field(default_factory=list)
    derived_facts: list[str] = Field(default_factory=list)
    goal_status: GoalStatus = "open"
    covered_requirements: list[str] = Field(default_factory=list)
    can_continue_forward: bool = False
    trace: list[str] = Field(default_factory=list)
