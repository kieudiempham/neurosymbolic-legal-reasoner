"""HTTP-facing response models for the QA API (used by orchestrator + FastAPI)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from schemas.answer import FinalAnswer
from schemas.clarification import ClarificationArtifact, ClarificationTarget
from schemas.evidence import EvidenceBundle
from schemas.evaluation_log import QAEvaluationLogArtifact, build_evaluation_log_artifact
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.proof import ProofObject
from schemas.reasoning import ReasoningState
from schemas.verification import VerificationRecord


class ClarificationPrompt(BaseModel):
    fact_key: str
    question_text: str
    reason_hint: str = ""
    reason: str = ""
    target_kind: str = ""
    expected_type: str = ""
    related_rule_id: str = ""
    priority: int = 50
    options: list[str] = Field(default_factory=list)
    blocking_reason: str = ""


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
    evidence_bundle: EvidenceBundle | None = None
    answer: FinalAnswer | None = None
    reasoning_result: dict[str, Any] | None = None
    debug_trace: dict[str, Any] = Field(default_factory=dict)
    clarification_artifact: ClarificationArtifact | None = None
    evaluation_log: QAEvaluationLogArtifact | None = None

    @model_validator(mode="after")
    def _populate_clarification_artifact(self) -> "AskResponse":
        if self.clarification_artifact is None:
            targets = [
                ClarificationTarget(
                    fact_key=p.fact_key,
                    target_kind=p.target_kind,
                    expected_type=p.expected_type,
                )
                for p in self.clarification_questions
            ]
            self.clarification_artifact = ClarificationArtifact(
                needs_clarification=self.needs_clarification,
                clarification_targets=targets,
                clarification_question=[p.question_text for p in self.clarification_questions if p.question_text],
                rationale=[(p.reason or p.reason_hint) for p in self.clarification_questions if (p.reason or p.reason_hint)],
            )
        return self

    @model_validator(mode="after")
    def _populate_evaluation_log(self) -> "AskResponse":
        if self.evaluation_log is None:
            query_text = None
            if isinstance(self.debug_trace, dict):
                q = self.debug_trace.get("query_text")
                if isinstance(q, str) and q.strip():
                    query_text = q.strip()
            self.evaluation_log = build_evaluation_log_artifact(
                session_id=self.session_id,
                query_text=query_text,
                layer1=self.layer1,
                layer2=self.layer2,
                retrieved_rules=self.retrieved_rules,
                selected_rule=self.selected_rule,
                reasoning=self.reasoning,
                proof=self.proof,
                answer=self.answer,
                needs_clarification=self.needs_clarification,
                clarification_questions=self.clarification_questions,
                verification_trace=self.verification_trace,
                debug_trace=self.debug_trace,
            )
        return self


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
    evidence_bundle: EvidenceBundle | None = None
    answer: FinalAnswer | None = None
    reasoning_result: dict[str, Any] | None = None
    debug_trace: dict[str, Any] = Field(default_factory=dict)
    clarification_artifact: ClarificationArtifact | None = None
    evaluation_log: QAEvaluationLogArtifact | None = None

    @model_validator(mode="after")
    def _populate_clarification_artifact(self) -> "ClarifyResponse":
        if self.clarification_artifact is None:
            targets = [
                ClarificationTarget(
                    fact_key=p.fact_key,
                    target_kind=p.target_kind,
                    expected_type=p.expected_type,
                )
                for p in self.clarification_questions
            ]
            self.clarification_artifact = ClarificationArtifact(
                needs_clarification=self.needs_clarification,
                clarification_targets=targets,
                clarification_question=[p.question_text for p in self.clarification_questions if p.question_text],
                rationale=[(p.reason or p.reason_hint) for p in self.clarification_questions if (p.reason or p.reason_hint)],
            )
        return self

    @model_validator(mode="after")
    def _populate_evaluation_log(self) -> "ClarifyResponse":
        if self.evaluation_log is None:
            query_text = None
            if isinstance(self.debug_trace, dict):
                q = self.debug_trace.get("query_text")
                if isinstance(q, str) and q.strip():
                    query_text = q.strip()
            self.evaluation_log = build_evaluation_log_artifact(
                session_id=self.session_id,
                query_text=query_text,
                layer1=self.layer1,
                layer2=self.layer2,
                retrieved_rules=self.retrieved_rules,
                selected_rule=self.selected_rule,
                reasoning=self.reasoning,
                proof=self.proof,
                answer=self.answer,
                needs_clarification=self.needs_clarification,
                clarification_questions=self.clarification_questions,
                verification_trace=self.verification_trace,
                debug_trace=self.debug_trace,
            )
        return self


class HealthResponse(BaseModel):
    status: str = "ok"
    rulebase_loaded: bool = False
    rule_count: int = 0
    evidence_chunks: int = 0
    domains_loaded: list[str] = Field(default_factory=list)
    shared_layer_loaded: bool = False
    rule_counts_by_domain: dict[str, int] = Field(default_factory=dict)
    registry_first: bool = False
    phase3_bridge_inference: bool = True
    phase3_temporal_policy: bool = True
    phase3_conflict_policy: bool = True
    namespacing_mode: str = "global_rule_key_v1"
    default_reasoning_date_note: str = ""


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
