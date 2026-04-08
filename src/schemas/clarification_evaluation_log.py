"""Extension schema for clarification evaluation metrics in evaluation log."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ClarificationEvaluationMetrics(BaseModel):
    """Metrics from clarification two-phase evaluation."""

    asked_clarification: bool = Field(
        ...,
        description="Whether clarification was needed and asked in phase 1",
    )
    clarification_targets: list[str] = Field(
        default_factory=list,
        description="List of missing fact keys/targets that required clarification",
    )
    gold_clarification_answer: str | None = Field(
        default=None,
        description="Gold clarification answer injected in phase 2",
    )
    # Before clarification (phase 1)
    answer_before: str | None = Field(
        default=None,
        description="Final answer from phase 1 (before clarification)",
    )
    proof_before: dict[str, Any] | None = Field(
        default=None,
        description="Reasoning proof from phase 1",
    )
    final_status_before: str | None = Field(
        default=None,
        description="QA status from phase 1 (needs_clarification/answered/failed/open)",
    )
    # After clarification (phase 3)
    answer_after: str | None = Field(
        default=None,
        description="Final answer from phase 3 (after clarification)",
    )
    proof_after: dict[str, Any] | None = Field(
        default=None,
        description="Reasoning proof from phase 3",
    )
    final_status_after: str | None = Field(
        default=None,
        description="QA status from phase 3",
    )
    # Gain metrics
    gained_answer: bool = Field(
        default=False,
        description="Changed from no/empty answer to non-empty answer",
    )
    gained_proof: bool = Field(
        default=False,
        description="Proof became more complete/correct after clarification",
    )
    resolved_after_clarification: bool = Field(
        default=False,
        description="Status changed from non-answered to answered",
    )


def build_clarification_evaluation_log(
    eval_result: Any,
) -> ClarificationEvaluationMetrics:
    """
    Build clarification evaluation metrics from ClarificationEvaluationResult.

    Intended for export to evaluation_log.clarification_evaluation field.
    """
    return ClarificationEvaluationMetrics(
        asked_clarification=eval_result.asked_clarification,
        clarification_targets=eval_result.clarification_targets,
        gold_clarification_answer=eval_result.gold_clarification_answer,
        answer_before=eval_result.answer_before,
        proof_before=eval_result.proof_before,
        final_status_before=eval_result.final_status_before,
        answer_after=eval_result.answer_after,
        proof_after=eval_result.proof_after,
        final_status_after=eval_result.final_status_after,
        gained_answer=eval_result.gained_answer,
        gained_proof=eval_result.gained_proof,
        resolved_after_clarification=eval_result.resolved_after_clarification,
    )
