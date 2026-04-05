"""Evidence snippets from corpus (RAG support only, not rule generation)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvidenceSnippet(BaseModel):
    chunk_id: str
    text: str
    source_doc: str | None = None
    article_clause: str | None = None
    rule_id: str | None = None
    score: float = 0.0
    retrieval_reason: str = ""
    linked_rule_id: str | None = None
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    doc_id: str | None = None
    article: str | None = None
    clause: str | None = None
    point: str | None = None
