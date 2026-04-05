"""Structured legal citations for frontend (links, PDF anchors, excerpts)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PdfAnchor(BaseModel):
    page: int | None = None
    bbox: list[float] | None = None
    anchor_text: str | None = None


class OpenPdfPayload(BaseModel):
    """Payload for opening a PDF viewer / modal at the right place."""

    doc_id: str | None = None
    page: int | None = None
    source_ref: str | None = None
    chunk_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class LegalCitation(BaseModel):
    citation_id: str
    label: str
    display_label: str
    doc_id: str | None = None
    source_ref: str | None = None
    article: str | None = None
    clause: str | None = None
    point: str | None = None
    excerpt: str = ""
    tooltip_excerpt: str | None = None
    pdf_anchor: PdfAnchor | None = None
    open_pdf_payload: OpenPdfPayload | None = None
    chunk_id: str | None = None


class CitationSpan(BaseModel):
    """Maps a substring of answer_text to a citation_id for clickable UI."""

    citation_id: str
    label: str
    text_span: str
    start: int | None = None
    end: int | None = None
