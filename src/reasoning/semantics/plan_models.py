"""Structured plans, missing items, forward/backward results, evaluation hooks (Pydantic)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field

FailureReason = Literal[
    "positive_condition_missing",
    "negative_condition_blocked",
    "unless_condition_unknown",
    "exception_triggered",
    "exception_unknown",
    "constraint_failed",
    "constraint_missing_input",
    "constraint_unknown",
    "goal_not_derived",
    "unification_broken",
    "none",
]

ConstraintEvalStatus = Literal["satisfied", "failed", "missing_input", "unknown"]


class MissingAtom(BaseModel):
    """Missing ground atom (positive / unless / etc.)."""

    role: Literal["positive", "unless", "other"] = "positive"
    atom: dict[str, Any]
    rule_id: str
    askable: bool = True
    expected_type: str = "boolean"
    question: str = ""


class MissingExceptionInput(BaseModel):
    kind: Literal["exception_input"] = "exception_input"
    atom: dict[str, Any]
    rule_id: str
    askable: bool = True
    expected_type: str = "boolean"
    question: str = ""


class MissingConstraintInput(BaseModel):
    kind: Literal["constraint_input"] = "constraint_input"
    target: str
    constraint_type: str
    atom: dict[str, Any] | None = None
    expected_type: str = "number"
    question: str = ""
    rule_id: str = ""
    session_key_hint: str = ""


class ClarificationRequest(BaseModel):
    """Unified clarification slot (API-friendly)."""

    kind: Literal["fact", "exception_input", "constraint_input", "negative_check"]
    target: str = ""
    atom: dict[str, Any] | None = None
    expected_type: str = "boolean"
    question: str = ""
    related_rule_id: str = ""


class ConstraintEvaluationResult(BaseModel):
    constraint_type: str
    status: ConstraintEvalStatus
    detail: str = ""
    session_key: str = ""
    numeric_lookup: dict[str, Any] | None = None


class ProofStepRecord(BaseModel):
    derived_atom: list[Any] = Field(default_factory=list)
    rule_id: str = ""
    supporting_atoms: list[list[Any]] = Field(default_factory=list)
    negative_checks: list[dict[str, Any]] = Field(default_factory=list)
    exception_checks: list[dict[str, Any]] = Field(default_factory=list)
    applied_constraints: list[dict[str, Any]] = Field(default_factory=list)
    substitution: dict[str, Any] = Field(default_factory=dict)
    source_ref: str | None = None
    status: str = "ok"
    failure_reason: str | None = None


class FailedPathRecord(BaseModel):
    """One failed candidate path — user-facing explanation + clarification priority."""

    rule_id: str
    goal_atom: list[Any] = Field(default_factory=list)
    failure_reason: FailureReason = "goal_not_derived"
    failure_detail: str = ""
    missing_atoms: list[dict[str, Any]] = Field(default_factory=list)
    missing_constraint_inputs: list[str] = Field(default_factory=list)
    blocking_negative_atoms: list[dict[str, Any]] = Field(default_factory=list)
    triggered_exception_atoms: list[dict[str, Any]] = Field(default_factory=list)
    failed_constraints: list[dict[str, Any]] = Field(default_factory=list)
    supporting_atoms: list[dict[str, Any]] = Field(default_factory=list)
    source_ref: str | None = None
    user_message_hint: str = ""
    clarification_priority: int = 50


class ForwardPathResult(BaseModel):
    rule_id: str
    goal_reached: bool
    conclusion: str = ""
    failure_reason: FailureReason = "none"
    failure_detail: str = ""
    substitution: dict[str, Any] = Field(default_factory=dict)
    proof_steps: list[ProofStepRecord] = Field(default_factory=list)
    constraint_traces: list[ConstraintEvaluationResult] = Field(default_factory=list)
    known_atoms_snapshot: list[str] = Field(default_factory=list)
    derived_atoms: list[str] = Field(default_factory=list)
    goal_atom: list[Any] = Field(default_factory=list)
    supporting_atoms: list[dict[str, Any]] = Field(default_factory=list)
    blocking_negative_atoms: list[dict[str, Any]] = Field(default_factory=list)
    triggered_exception_atoms: list[dict[str, Any]] = Field(default_factory=list)
    failed_path_records: list[FailedPathRecord] = Field(default_factory=list)

    @computed_field
    @property
    def failed_paths(self) -> list[str]:
        return [r.rule_id for r in self.failed_path_records]


class ReasoningFailure(BaseModel):
    reason: FailureReason
    detail: str = ""
    rule_id: str | None = None
    step: str | None = None


class EvaluationHooks(BaseModel):
    """Hooks for offline metrics / audits — populated by runtime, not full eval pipeline."""

    goal_achievement_trace: dict[str, Any] = Field(default_factory=dict)
    requirement_correctness: dict[str, Any] = Field(default_factory=dict)
    missing_fact_correctness: dict[str, Any] = Field(default_factory=dict)
    constraint_evaluation_trace: list[dict[str, Any]] = Field(default_factory=list)
    proof_validity_trace: dict[str, Any] = Field(default_factory=dict)
    failure_trace: list[dict[str, Any]] = Field(default_factory=list)


class BackwardCandidate(BaseModel):
    rule_id: str
    retrieval_score: float = 0.0
    unification_score: float = 0.0
    total_score: float = 0.0
    substitution: dict[str, Any] = Field(default_factory=dict)
    grounded_atoms: list[dict[str, Any]] = Field(default_factory=list)
    missing_atoms: list[MissingAtom] = Field(default_factory=list)
    negative_checks: list[dict[str, Any]] = Field(default_factory=list)
    exception_checks: list[dict[str, Any]] = Field(default_factory=list)
    constraint_checks: list[dict[str, Any]] = Field(default_factory=list)
    missing_constraint_inputs: list[MissingConstraintInput] = Field(default_factory=list)
    missing_exception_inputs: list[MissingExceptionInput] = Field(default_factory=list)
    missing_fact_keys: list[str] = Field(default_factory=list)
    status: Literal["ready", "blocked", "needs_input"] = "needs_input"
    unification_failure: str | None = None


class BackwardPlan(BaseModel):
    goal_atom: list[Any] = Field(default_factory=list)
    candidates: list[BackwardCandidate] = Field(default_factory=list)
    substitutions: list[dict[str, Any]] = Field(default_factory=list)
    evaluation: EvaluationHooks = Field(default_factory=EvaluationHooks)
