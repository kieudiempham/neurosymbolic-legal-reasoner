"""HTTP-facing response models for the QA API (used by orchestrator + FastAPI)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from schemas.answer import FinalAnswer
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.proof import ProofObject
from schemas.reasoning import ReasoningState
from schemas.verification import VerificationRecord


class ClarificationPrompt(BaseModel):
    fact_key: str
    question_text: str
    reason_hint: str = ""


class AskResponse(BaseModel):
    session_id: str
    needs_clarification: bool = False
    clarification_questions: list[ClarificationPrompt] = Field(default_factory=list)
    layer1: Layer1Parse | None = None
    layer2: Layer2Parse | None = None
    verification_trace: list[VerificationRecord] = Field(default_factory=list)
    retrieved_rules: list[dict[str, Any]] = Field(default_factory=list)
    selected_rule: dict[str, Any] | None = None
    reasoning: ReasoningState | None = None
    proof: ProofObject | None = None
    answer: FinalAnswer | None = None
    debug_trace: dict[str, Any] = Field(default_factory=dict)


class ClarifyResponse(BaseModel):
    session_id: str
    needs_clarification: bool = False
    clarification_questions: list[ClarificationPrompt] = Field(default_factory=list)
    layer1: Layer1Parse | None = None
    layer2: Layer2Parse | None = None
    verification_trace: list[VerificationRecord] = Field(default_factory=list)
    retrieved_rules: list[dict[str, Any]] = Field(default_factory=list)
    selected_rule: dict[str, Any] | None = None
    reasoning: ReasoningState | None = None
    proof: ProofObject | None = None
    answer: FinalAnswer | None = None
    debug_trace: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str = "ok"
    rulebase_loaded: bool = False
    rule_count: int = 0
    evidence_chunks: int = 0


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
