"""NeSy verification records."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

VerificationMode = Literal[
    "parse_verification",
    "backward_verification",
    "forward_verification",
    "answer_verification",
]

NLILabel = Literal["entailment", "contradiction", "neutral"]

FusionDecision = Literal["ACCEPT", "REJECT", "REPAIR"]


class NLIResult(BaseModel):
    label: NLILabel = "neutral"
    score: float = 0.5


class VerificationRecord(BaseModel):
    mode: VerificationMode
    symbolic_result: str = "unknown"
    symbolic_ok: bool = False
    nli_result: NLIResult | None = None
    final_decision: FusionDecision = "REJECT"
    diagnostics: list[str] = Field(default_factory=list)
    repair_target: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
