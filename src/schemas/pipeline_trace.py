"""Structured pipeline trace for single-question runs and batch experiments."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

PipelineTurn = Literal["ask", "clarify"]
StepStatus = Literal["success", "failed", "skipped"]


class PipelineStepTrace(BaseModel):
    step_name: str
    status: StepStatus = "success"
    started_at: str = ""
    ended_at: str = ""
    duration_ms: float = 0.0
    input_summary: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    decision: str | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PipelineTrace(BaseModel):
    trace_id: str
    question_text: str = ""
    session_id: str | None = None
    turn: PipelineTurn = "ask"
    steps: list[PipelineStepTrace] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
