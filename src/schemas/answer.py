"""Final answer payload."""

from __future__ import annotations

from pydantic import BaseModel, Field

from schemas.evidence import EvidenceSnippet


class FinalAnswer(BaseModel):
    answer_text: str = ""
    conclusion: str = ""
    proof_summary: str = ""
    evidence_snippets: list[EvidenceSnippet] = Field(default_factory=list)
    confidence: float = 0.0
    verification_summary: str = ""
