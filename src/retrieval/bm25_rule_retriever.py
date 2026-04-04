"""Lexical (BM25) stage for rule candidates — combined with structured signals in ``rule_retriever.retrieve_rules``."""

from __future__ import annotations

from retrieval.hybrid_rule_ranker import bm25_scores_for_documents
from retrieval.rule_retriever import rule_document_text
from schemas.rule import RuleRecord


def bm25_lexical_scores(rules: list[RuleRecord], query: str) -> list[float]:
    """Return raw BM25 scores parallel to ``rules`` (same order)."""
    if not rules:
        return []
    documents = [rule_document_text(r) for r in rules]
    return bm25_scores_for_documents(documents, query)
