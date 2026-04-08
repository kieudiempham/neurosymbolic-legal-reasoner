"""NeSy verification records — v5 multi-mode + diagnostic taxonomy + repair routing."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

VerificationMode = Literal[
    "parse_verification",
    "rule_verification",
    "backward_verification",
    "forward_verification",
    "answer_verification",
]

NLILabel = Literal["entailment", "contradiction", "neutral"]

FusionDecision = Literal["ACCEPT", "REJECT", "REPAIR"]


class NLIResult(BaseModel):
    label: NLILabel = "neutral"
    score: float = 0.5
    scores: dict[str, float] | None = None


class VerificationRecord(BaseModel):
    """Single-mode verification outcome — NeSy Verify Engine (source of truth)."""

    mode: VerificationMode
    symbolic_result: str = "unknown"
    symbolic_ok: bool = False
    nli_result: NLIResult | None = None
    final_decision: FusionDecision = "REJECT"
    diagnostics: list[str] = Field(default_factory=list)
    repair_target: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
    # v5 extended fields (optional for JSON back-compat)
    diagnostic_errors: list[str] = Field(
        default_factory=list,
        description="Taxonomy codes: parse_*, rule_*, backward_*, forward_*, answer_*",
    )
    repair_target_module: str | None = None
    repair_hint: str = ""
    repair_payload: dict[str, Any] = Field(default_factory=dict)
    decision: FusionDecision | None = None
    reasons: list[str] = Field(default_factory=list)
    repair_hints: list[str] = Field(default_factory=list)
    repair_applied: bool = False
    rerun_stage: str | None = None
    repair_diagnostics: dict[str, Any] = Field(default_factory=dict)
    semantic_scores: dict[str, float] = Field(default_factory=dict)
    symbolic_checks: dict[str, Any] = Field(default_factory=dict)
    normalized_inputs: dict[str, Any] = Field(default_factory=dict)
    verbalized_texts: dict[str, str] = Field(default_factory=dict)
    trace: list[str] = Field(default_factory=list)


class VerificationResult(BaseModel):
    """Legacy stub type — prefer VerificationRecord for new code."""

    ok: bool = False
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
