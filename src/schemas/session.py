"""Session state (in-memory demo)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from schemas.answer import FinalAnswer
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.proof import ProofObject
from schemas.reasoning import ReasoningState
from schemas.rule import RuleRecord
from schemas.verification import VerificationRecord


class SessionState(BaseModel):
    session_id: str
    original_question: str = ""
    user_facts: list[str] = Field(default_factory=list)
    layer1: Layer1Parse | None = None
    layer2: Layer2Parse | None = None
    known_facts: dict[str, Any] = Field(default_factory=dict)
    missing_facts: list[str] = Field(default_factory=list)
    clarification_questions: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_rules: list[RuleRecord] = Field(default_factory=list)
    selected_rule: RuleRecord | None = None
    reasoning: ReasoningState | None = None
    proof: ProofObject | None = None
    answer: FinalAnswer | None = None
    verification_logs: list[VerificationRecord] = Field(default_factory=list)
    pipeline_trace: dict[str, Any] = Field(default_factory=dict)
