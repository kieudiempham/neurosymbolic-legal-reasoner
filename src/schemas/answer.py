"""Final answer payload."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from schemas.citation import CitationSpan, LegalCitation
from schemas.evidence import EvidenceSnippet


class FinalAnswer(BaseModel):
    answer_text: str = ""
    conclusion: str = ""
    proof_summary: str = ""
    evidence_snippets: list[EvidenceSnippet] = Field(default_factory=list)
    confidence: float = 0.0
    verification_summary: str = ""
    generation_mode: str = "template_grounded"
    """template_grounded | llm_grounded — both must use only conclusion/proof/evidence passed in."""

    legal_citations: list[LegalCitation] = Field(default_factory=list)
    citation_spans: list[CitationSpan] = Field(default_factory=list)
    answer_sections: dict[str, str] = Field(default_factory=dict)
    """Keys: opening, conclusion_lead, analysis, closing — mirror structured advice layout."""

    extra: dict[str, Any] = Field(default_factory=dict)
