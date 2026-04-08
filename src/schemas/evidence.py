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
    source_ref: str | None = None
    page: int | None = None


class EvidenceRecord(BaseModel):
    evidence_id: str
    source_type: str = "corpus_chunk"
    statute_id: str | None = None
    article: str | None = None
    clause: str | None = None
    text_span: str = ""
    linked_subgoal: str | None = None
    support_score: float | None = None
    contradiction_score: float | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    bundle_id: str
    query_text: str = ""
    selected_rule_id: str | None = None
    requirement_set: list[str] = Field(default_factory=list)
    proof_subgoals: list[str] = Field(default_factory=list)
    items: list[EvidenceRecord] = Field(default_factory=list)
    linkage_map: dict[str, list[str]] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
