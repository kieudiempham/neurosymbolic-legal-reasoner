"""Unified QA outcome for single-question API and batch experiment records."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.http_response import ClarificationPrompt
from schemas.pipeline_trace import PipelineTrace

QAStatus = Literal["answered", "needs_clarification", "failed"]


class FinalAnswerSummary(BaseModel):
    """Subset of FinalAnswer for stable API / batch JSON."""

    answer_text: str = ""
    generation_mode: str = ""
    legal_citations: list[dict[str, Any]] = Field(default_factory=list)
    proof_summary: str = ""
    verification_summary: str = ""


class QAResponse(BaseModel):
    """One end-to-end turn (ask or clarify)."""

    status: QAStatus
    question_text: str = ""
    session_id: str = ""
    trace_id: str | None = None
    final_answer: FinalAnswerSummary | None = None
    clarification_prompts: list[ClarificationPrompt] = Field(default_factory=list)
    reason: str | None = None
    failure_code: str | None = None
    current_trace_summary: dict[str, Any] = Field(default_factory=dict)
    trace_summary: dict[str, Any] = Field(default_factory=dict)
    pipeline_trace: PipelineTrace | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class QARunRecord(BaseModel):
    """Machine-readable row for batch / experiment aggregation."""

    qid: str | None = None
    status: str = ""
    session_id: str = ""
    trace_id: str | None = None
    answer_text: str | None = None
    selected_rule_ids: list[str] = Field(default_factory=list)
    goal: dict[str, Any] | None = None
    missing_facts: list[str] = Field(default_factory=list)
    verification_decisions: dict[str, str] = Field(default_factory=dict)
    run_config: dict[str, Any] | None = None
    trace_file: str | None = None
    failure_reason: str | None = None
